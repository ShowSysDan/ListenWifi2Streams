"""
stream_server.py — Per-channel HTTP MP3 stream server.

Each ListenWifi audio channel gets its own ChannelStreamServer bound to a
dedicated TCP port (6001, 6002, …).  VLC (or any HTTP audio client) connects
with:
    vlc http://<host>:<port>/

Architecture:
    Python (RTP receiver)
        → feed_pcm(pcm_bytes)          [raw 16-bit LE PCM, 48 kHz, mono]
        → ffmpeg stdin                 [PCM → MP3 transcoding]
        → ffmpeg stdout                [MP3 byte stream]
        → _broadcast_loop thread       [fans out to all connected clients]
        → HTTP response sockets        [one per VLC/client connection]

ICY metadata headers (understood by VLC, Winamp, etc.) carry the channel name
so the player's "Now Playing" display shows the ListenWifi channel title.
"""

import logging
import queue
import shutil
import socket
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

logger = logging.getLogger(__name__)

FFMPEG_SAMPLE_RATE = 48000
FFMPEG_CHANNELS    = 1       # mono
FFMPEG_BITRATE     = "128k"
READ_CHUNK         = 4096    # bytes read from ffmpeg stdout per iteration
CLIENT_QUEUE_SIZE  = 200     # max queued MP3 chunks per connected client


def _find_ffmpeg() -> str:
    """Return the path to ffmpeg, preferring a local copy over PATH."""
    local = shutil.which("ffmpeg")
    if local:
        return local
    raise FileNotFoundError(
        "ffmpeg not found. Install it (winget install ffmpeg) or place ffmpeg.exe "
        "in the listenifi_monitor directory."
    )


class ChannelStreamServer:
    """
    HTTP server that streams a single ListenWifi audio channel as MP3.

    Call start() once when the channel is discovered.
    Call feed_pcm() continuously as decoded PCM arrives from RTPStreamReceiver.
    Call stop() to clean up.
    """

    def __init__(self, port: int, channel_number: str, title: str):
        self.port           = port
        self.channel_number = channel_number
        self.title          = title

        self._ffmpeg: Optional[subprocess.Popen] = None
        self._http:   Optional[HTTPServer]        = None

        # Each connected client gets its own Queue of MP3 bytes chunks
        self._clients: list[queue.Queue] = []
        self._clients_lock = threading.Lock()

        # Stats
        self.bytes_sent      = 0
        self.client_count    = 0
        self.packets_in      = 0

        self._stopped = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start ffmpeg + HTTP server in background daemon threads."""
        ffmpeg_cmd = _find_ffmpeg()
        self._ffmpeg = subprocess.Popen(
            [
                ffmpeg_cmd,
                "-loglevel", "quiet",
                # Input: raw PCM from stdin
                "-f", "s16le",
                "-ar", str(FFMPEG_SAMPLE_RATE),
                "-ac", str(FFMPEG_CHANNELS),
                "-i", "pipe:0",
                # Output: MP3 to stdout
                "-f", "mp3",
                "-b:a", FFMPEG_BITRATE,
                "-reservoir", "0",          # lower latency
                "-metadata", f"title={self.title}",
                "-metadata", "artist=ListenWifi Monitor",
                "pipe:1",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        logger.info("ffmpeg started for channel %s (%s)", self.channel_number, self.title)

        # Thread: read ffmpeg output and broadcast to clients
        threading.Thread(
            target=self._broadcast_loop,
            name=f"broadcast-{self.port}",
            daemon=True,
        ).start()

        # Thread: HTTP server
        server = self   # capture for handler closure
        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                server._handle_client(self)
            def log_message(self, fmt, *args):
                logger.debug("HTTP [port %d] " + fmt, server.port, *args)

        self._http = HTTPServer(("0.0.0.0", self.port), _Handler)
        threading.Thread(
            target=self._http.serve_forever,
            name=f"http-{self.port}",
            daemon=True,
        ).start()
        logger.info(
            "Stream server started: channel '%s' on port %d", self.title, self.port
        )

    def stop(self) -> None:
        """Shut down ffmpeg and the HTTP server."""
        self._stopped = True
        if self._ffmpeg:
            try:
                self._ffmpeg.stdin.close()
            except Exception:
                pass
            self._ffmpeg.terminate()
            self._ffmpeg = None
        if self._http:
            self._http.shutdown()
            self._http = None
        # Unblock all waiting client queues
        with self._clients_lock:
            for q in self._clients:
                try:
                    q.put_nowait(None)  # sentinel → client thread exits
                except queue.Full:
                    pass
            self._clients.clear()
        logger.info("Stream server stopped for channel %s", self.channel_number)

    def feed_pcm(self, pcm_bytes: bytes) -> None:
        """
        Write decoded PCM bytes to ffmpeg's stdin.
        Called from RTPStreamReceiver's background thread.
        """
        if self._ffmpeg is None or self._stopped:
            return
        self.packets_in += 1
        try:
            self._ffmpeg.stdin.write(pcm_bytes)
        except (BrokenPipeError, OSError):
            logger.warning(
                "ffmpeg stdin closed for channel %s — stream may have crashed",
                self.channel_number,
            )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _broadcast_loop(self) -> None:
        """Read MP3 chunks from ffmpeg stdout and distribute to all clients."""
        while not self._stopped:
            if self._ffmpeg is None:
                break
            try:
                chunk = self._ffmpeg.stdout.read(READ_CHUNK)
            except Exception:
                break
            if not chunk:
                break

            self.bytes_sent += len(chunk)
            with self._clients_lock:
                dead = []
                for q in self._clients:
                    try:
                        q.put_nowait(chunk)
                    except queue.Full:
                        # Client is too slow — drop chunk for this client
                        pass
                    except Exception:
                        dead.append(q)
                for q in dead:
                    self._clients.remove(q)

    def _handle_client(self, handler: BaseHTTPRequestHandler) -> None:
        """
        Serve one HTTP streaming connection.
        Blocks until the client disconnects.
        """
        # Build ICY / HTTP response headers
        handler.send_response(200)
        handler.send_header("Content-Type", "audio/mpeg")
        handler.send_header("icy-name",     self.title)
        handler.send_header("icy-pub",      "1")
        handler.send_header("icy-br",       "128")
        handler.send_header("Cache-Control", "no-cache, no-store")
        handler.send_header("Connection",   "close")
        handler.end_headers()

        client_q: queue.Queue = queue.Queue(maxsize=CLIENT_QUEUE_SIZE)
        with self._clients_lock:
            self._clients.append(client_q)
            self.client_count += 1

        addr = handler.client_address
        logger.info(
            "Client connected to channel '%s' (port %d) from %s:%d",
            self.title, self.port, *addr,
        )

        try:
            while not self._stopped:
                try:
                    chunk = client_q.get(timeout=2.0)
                except queue.Empty:
                    # Send a keepalive / check if still connected
                    try:
                        handler.wfile.write(b"")
                        handler.wfile.flush()
                    except Exception:
                        break
                    continue

                if chunk is None:  # sentinel from stop()
                    break
                try:
                    handler.wfile.write(chunk)
                    handler.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    break
        finally:
            with self._clients_lock:
                if client_q in self._clients:
                    self._clients.remove(client_q)
            logger.info(
                "Client disconnected from channel '%s' (port %d) from %s:%d",
                self.title, self.port, *addr,
            )

    @property
    def active_clients(self) -> int:
        with self._clients_lock:
            return len(self._clients)
