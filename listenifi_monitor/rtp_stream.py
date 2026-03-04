"""
rtp_stream.py — RTP/UDP receiver with Opus decoding.

Receives RTP packets on a UDP socket, strips the RTP header, decodes the Opus
payload to raw 16-bit signed PCM (48 kHz, mono), and calls a user-supplied
callback for each decoded frame.

RTP packet structure (RFC 3550):
    Byte 0:  V(2) P(1) X(1) CC(4)
    Byte 1:  M(1) PT(7)
    Bytes 2-3:  Sequence number
    Bytes 4-7:  Timestamp
    Bytes 8-11: SSRC identifier
    [Optional: CSRC list, extension header]
    Payload: Opus-encoded audio frame
"""

import ctypes
import logging
import os
import socket
import struct
import threading
from typing import Callable

logger = logging.getLogger(__name__)

RTP_MIN_HEADER = 12  # bytes
OPUS_FRAME_SIZE = 960  # samples per frame at 48 kHz (= 20 ms)
OPUS_SAMPLE_RATE = 48000
OPUS_CHANNELS = 1  # mono; most ListenWifi channels are mono

# Maximum UDP datagram we'll read (Opus frames are typically < 1500 bytes)
MAX_UDP_BYTES = 4096

# Solicitation protocol constants (from Android SDK Constants.class binary analysis):
#   Constants.UDP_PORT = 16384
#   Constants.TOKEN_SOLICITATION = "TokenSolicitation"
#
# After the HTTP stream request succeeds, the server waits for a UDP solicitation
# packet sent FROM the client's RTP receive port TO server_ip:SOLICITATION_PORT.
# This replaced the old ICMP ping mechanism (SDK v7.1 / v5.1 changelog).
# The packet payload is the TokenSolicitation string from the HTTP response,
# encoded as UTF-8 bytes (empty bytes for public channels with no token).
SOLICITATION_PORT = 16384

# ---------------------------------------------------------------------------
# Pre-load opus shared library from the script directory before opuslib tries
# to find it.  On Windows, ctypes only searches PATH — not the script folder —
# so opus.dll placed alongside app.py would otherwise be silently ignored.
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))
for _dll_name in ("opus.dll", "libopus.dll", "libopus-0.dll"):
    _dll_path = os.path.join(_here, _dll_name)
    if os.path.exists(_dll_path):
        try:
            ctypes.CDLL(_dll_path)
            logger.debug("Pre-loaded %s from script directory", _dll_name)
        except OSError as _e:
            logger.warning("Found %s but could not load it: %s", _dll_path, _e)
        break

# Attempt to import opuslib; degrade gracefully if libopus is not installed
try:
    import opuslib
    _OPUS_AVAILABLE = True
except Exception:
    _OPUS_AVAILABLE = False
    logger.warning(
        "opuslib not available — Opus decoding disabled. "
        "Install opuslib and ensure opus.dll / libopus.so is present."
    )


def get_local_ip(target: str = "8.8.8.8") -> str:
    """
    Return this machine's IP on the interface used to reach *target*.

    Pass the ListenWifi server's IP so that on multi-homed machines the
    correct interface address is returned — e.g. the 172.16.x.x address
    rather than the default-route address — ensuring RTP packets are
    delivered to an interface the server can actually reach.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((target, 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def parse_rtp(data: bytes) -> bytes | None:
    """
    Strip the RTP header from a raw UDP payload.

    Returns the Opus payload bytes, or None if the packet is too short or malformed.
    """
    if len(data) < RTP_MIN_HEADER:
        return None

    b0 = data[0]
    version = (b0 >> 6) & 0x03
    if version != 2:
        return None  # not a valid RTP packet

    has_extension = (b0 >> 4) & 0x01
    csrc_count    = b0 & 0x0F

    offset = RTP_MIN_HEADER + csrc_count * 4

    if has_extension:
        # Extension header: 2 bytes profile, 2 bytes length (in 32-bit words)
        if len(data) < offset + 4:
            return None
        ext_len = struct.unpack_from(">H", data, offset + 2)[0]
        offset += 4 + ext_len * 4

    if offset >= len(data):
        return None  # no payload

    return data[offset:]


class RTPStreamReceiver:
    """
    Listens on a UDP port for incoming RTP/Opus packets, decodes them, and
    fires on_pcm(pcm_bytes: bytes) for each decoded frame.

    Each frame is 960 samples × 2 bytes = 1920 bytes of 16-bit signed little-endian PCM.

    Solicitation protocol (SDK v7.1 / v5.1, replacing ICMP ping):
      After binding the receive socket, a UDP solicitation packet is sent FROM
      that socket TO server_host:SOLICITATION_PORT (16384).  The server uses
      this to confirm the client is ready and starts sending RTP.  Using the
      same socket for both solicitation and receive avoids any race window.
    """

    def __init__(
        self,
        udp_port: int,
        on_pcm: Callable[[bytes], None],
        server_host: str = "",
        solicit_token: str = "",
    ):
        self._port = udp_port
        self._on_pcm = on_pcm
        self._server_host = server_host
        self._solicit_token = solicit_token
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._sock: socket.socket | None = None
        self.packets_received = 0
        self.frames_decoded = 0

        if _OPUS_AVAILABLE:
            self._decoder = opuslib.Decoder(OPUS_SAMPLE_RATE, OPUS_CHANNELS)
        else:
            self._decoder = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start receiving RTP in a background daemon thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._receive_loop,
            name=f"rtp-recv-{self._port}",
            daemon=True,
        )
        self._thread.start()
        logger.info("RTP receiver started on UDP port %d", self._port)

    def stop(self) -> None:
        """Signal the receive loop to exit and close the socket."""
        self._stop_event.set()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        logger.info("RTP receiver stopped (port %d)", self._port)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _receive_loop(self) -> None:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind(("0.0.0.0", self._port))
            self._sock.settimeout(1.0)
        except OSError as exc:
            logger.error("Cannot bind UDP socket on port %d: %s", self._port, exc)
            return

        # Send solicitation from the bound socket so the server can confirm the
        # client is listening and start sending RTP.  This replaces the old
        # ICMP-ping session validation (SDK changelog v7.1/v5.1).
        if self._server_host:
            payload = self._solicit_token.encode("utf-8") if self._solicit_token else b""
            try:
                self._sock.sendto(payload, (self._server_host, SOLICITATION_PORT))
                logger.info(
                    "Sent UDP solicitation → %s:%d (from port %d, token=%r)",
                    self._server_host, SOLICITATION_PORT, self._port,
                    self._solicit_token or "<empty>",
                )
            except OSError as exc:
                logger.warning(
                    "Solicitation to %s:%d failed: %s",
                    self._server_host, SOLICITATION_PORT, exc,
                )

        logger.debug("RTP receive loop running on port %d", self._port)

        while not self._stop_event.is_set():
            try:
                data, addr = self._sock.recvfrom(MAX_UDP_BYTES)
            except socket.timeout:
                continue
            except OSError:
                # Socket was closed by stop()
                break

            self.packets_received += 1
            payload = parse_rtp(data)
            if payload is None:
                continue

            if self._decoder is None:
                # No Opus support — pass raw payload as-is (for debugging)
                self._on_pcm(payload)
                continue

            try:
                pcm = self._decoder.decode(payload, OPUS_FRAME_SIZE)
                self.frames_decoded += 1
                self._on_pcm(pcm)
            except opuslib.OpusError as exc:
                logger.debug("Opus decode error (port %d): %s", self._port, exc)
            except Exception as exc:
                logger.warning("Unexpected decode error: %s", exc)




def bind_free_udp_port() -> tuple[int, socket.socket]:
    """
    Bind a UDP socket to an OS-assigned free port and return (port, socket).
    The caller is responsible for closing the socket or handing it to an
    RTPStreamReceiver.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", 0))
    port = s.getsockname()[1]
    s.close()  # receiver will re-bind; this just reserves the port number
    return port, s
