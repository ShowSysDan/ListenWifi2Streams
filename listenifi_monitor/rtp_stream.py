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

import logging
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


def get_local_ip() -> str:
    """Return this machine's LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
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
    """

    def __init__(self, udp_port: int, on_pcm: Callable[[bytes], None]):
        self._port = udp_port
        self._on_pcm = on_pcm
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
