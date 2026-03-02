"""
app.py — ListenWifi Audio Stream Monitor
Flask web dashboard (port 6000) + per-channel MP3 relay (ports 6001+).

Port assignment (IP-sorted):
  Channels are sorted by (server_ip_ascending, channel_number_ascending) and
  assigned ports 6001, 6002, … in that order.

  Example — 6 servers × 2 channels each:
    192.168.1.10  ch.1 → 6001
    192.168.1.10  ch.2 → 6002
    192.168.1.20  ch.1 → 6003
    192.168.1.20  ch.2 → 6004
    ...
    192.168.1.60  ch.2 → 6012

  If a new server is discovered that sorts lower than existing servers, all
  ports are recomputed and the affected stream servers are restarted.

Usage:
    python app.py
    open http://localhost:6000

VLC:
    vlc http://<your-ip>:<channel-port>/
"""

import logging
import socket
import threading
import time

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit

from api_client import ListenWifiClient
from discovery import ListenWifiDiscovery
from rtp_stream import RTPStreamReceiver, get_local_ip
from stream_server import ChannelStreamServer

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("app")

# ---------------------------------------------------------------------------
# Flask + SocketIO
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "listenifi-monitor-secret"
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# ---------------------------------------------------------------------------
# Ports
# ---------------------------------------------------------------------------
WEB_PORT    = 6000
STREAM_BASE = 6001

# ---------------------------------------------------------------------------
# Global state  (all mutations must hold _state_lock)
# ---------------------------------------------------------------------------
_state_lock = threading.Lock()

# mDNS name → {"name", "host", "port", "base_url", "friendly_name"}
_servers: dict[str, dict] = {}

# channel_number (str) → channel info dict (extended with our fields)
_channels: dict[str, dict] = {}

# channel_number → ChannelStreamServer
_stream_servers: dict[str, ChannelStreamServer] = {}

# channel_number → RTPStreamReceiver
_rtp_receivers: dict[str, RTPStreamReceiver] = {}

# channel_number → ListenWifiClient (the client for that channel's server)
_api_clients: dict[str, ListenWifiClient] = {}


# ---------------------------------------------------------------------------
# Sorting helpers
# ---------------------------------------------------------------------------

def _ip_to_int(ip: str) -> int:
    """Convert dotted IPv4 string to integer for numeric comparison."""
    try:
        parts = ip.split(".")
        return sum(int(p) << (8 * (3 - i)) for i, p in enumerate(parts))
    except Exception:
        return 0


def _ch_num_sort(number: str) -> int:
    """Sort key for channel numbers — numeric if possible, otherwise 0."""
    try:
        return int(number)
    except (ValueError, TypeError):
        return 0


def _sorted_servers_locked() -> list[dict]:
    """Servers sorted by IPv4 address ascending. Must hold _state_lock."""
    return sorted(_servers.values(), key=lambda s: _ip_to_int(s["host"]))


def _server_channels_sorted_locked(server_name: str) -> list[dict]:
    """Channels for one server sorted by channel number. Must hold _state_lock."""
    return sorted(
        [ch for ch in _channels.values() if ch.get("server_name") == server_name],
        key=lambda c: _ch_num_sort(c["number"]),
    )


# ---------------------------------------------------------------------------
# IP-sorted port assignment
# ---------------------------------------------------------------------------

def _recompute_all_ports_locked() -> None:
    """
    Assign stream ports 6001, 6002, … ordered by (server_ip_asc, channel_num_asc).

    Updates _channels[*]["stream_port"] and ["stream_url"] in-place.
    Must be called with _state_lock held.
    """
    local_ip = get_local_ip()
    port = STREAM_BASE
    for srv in _sorted_servers_locked():
        for ch in _server_channels_sorted_locked(srv["name"]):
            ch["stream_port"] = port
            ch["stream_url"]  = f"http://{local_ip}:{port}/"
            port += 1


# ---------------------------------------------------------------------------
# State serialisation
# ---------------------------------------------------------------------------

def _build_state() -> dict:
    """Serialise current state for SocketIO broadcast."""
    with _state_lock:
        srvs = _sorted_servers_locked()
        channels_list = []
        for srv in srvs:
            for ch in _server_channels_sorted_locked(srv["name"]):
                num  = ch["number"]
                recv = _rtp_receivers.get(num)
                ss   = _stream_servers.get(num)
                status = "idle"
                if recv and recv.is_running:
                    status = "active" if recv.packets_received > 0 else "requesting"
                channels_list.append({
                    **ch,
                    "server_host":    srv["host"],
                    "status":         status,
                    "active_clients": ss.active_clients if ss else 0,
                    "packets_in":     recv.packets_received if recv else 0,
                })
        servers_out = [
            {
                "name":          s["name"],
                "host":          s["host"],
                "port":          s["port"],
                "friendly_name": s.get("friendly_name") or s["name"].split(".")[0],
            }
            for s in srvs
        ]
    return {
        "servers":  servers_out,
        "channels": channels_list,
        "local_ip": get_local_ip(),
    }


def _emit_state() -> None:
    socketio.emit("state_update", _build_state())


# ---------------------------------------------------------------------------
# mDNS callbacks  (called from Zeroconf I/O thread)
# ---------------------------------------------------------------------------

def _on_server_added(server_info: dict) -> None:
    name = server_info["name"]
    logger.info("Server added: %s (%s)", name, server_info["host"])

    # Fetch channel list — network I/O, do outside the lock
    client   = ListenWifiClient(server_info["base_url"])
    channels = client.get_channels()
    logger.info("  %d channel(s) from %s", len(channels), server_info["host"])

    to_stop: list[ChannelStreamServer] = []
    to_start: list[ChannelStreamServer] = []

    with _state_lock:
        _servers[name] = server_info

        for ch in channels:
            num = ch["number"]
            if num not in _channels:
                _channels[num] = {
                    **ch,
                    "server_name": name,
                    "stream_port": 0,
                    "stream_url":  "",
                }
                _api_clients[num] = client

        # Recompute port assignments for ALL channels (may shift existing servers)
        _recompute_all_ports_locked()

        # Reconcile stream servers: stop any on the wrong port, start missing ones
        for num, ch in _channels.items():
            new_port = ch["stream_port"]
            existing = _stream_servers.get(num)

            if existing is None:
                srv = ChannelStreamServer(new_port, num, ch["title"])
                _stream_servers[num] = srv
                to_start.append(srv)
            elif existing.port != new_port:
                to_stop.append(existing)
                srv = ChannelStreamServer(new_port, num, ch["title"])
                _stream_servers[num] = srv
                to_start.append(srv)

    # Blocking I/O outside the lock
    for srv in to_stop:
        try:
            srv.stop()
        except Exception as exc:
            logger.error("Error stopping stream server: %s", exc)
    for srv in to_start:
        try:
            srv.start()
        except Exception as exc:
            logger.error("Error starting stream server: %s", exc)

    _emit_state()


def _on_server_removed(name: str) -> None:
    logger.info("Server removed: %s", name)

    to_stop: list[ChannelStreamServer] = []
    nums_to_remove: list[str] = []

    with _state_lock:
        _servers.pop(name, None)
        for num, ch in list(_channels.items()):
            if ch.get("server_name") == name:
                nums_to_remove.append(num)
        for num in nums_to_remove:
            recv = _rtp_receivers.pop(num, None)
            if recv:
                recv.stop()
            srv = _stream_servers.pop(num, None)
            if srv:
                to_stop.append(srv)
            _channels.pop(num, None)
            _api_clients.pop(num, None)

    for srv in to_stop:
        try:
            srv.stop()
        except Exception:
            pass

    _emit_state()


# ---------------------------------------------------------------------------
# Stream control
# ---------------------------------------------------------------------------

def _start_channel(channel_number: str) -> dict:
    """
    Start streaming a channel:
      1. Bind a free UDP port.
      2. Ask the ListenWifi server to unicast RTP to our IP:UDP port.
      3. RTPStreamReceiver feeds PCM into ChannelStreamServer → MP3 → VLC.
    """
    with _state_lock:
        ch     = _channels.get(channel_number)
        client = _api_clients.get(channel_number)
        srv    = _stream_servers.get(channel_number)

    if not ch or not client or not srv:
        return {"ok": False, "error": "Unknown channel"}

    # Stop any existing receiver for this channel
    with _state_lock:
        old = _rtp_receivers.pop(channel_number, None)
    if old:
        old.stop()

    # Let the OS pick a free UDP port
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("0.0.0.0", 0))
    udp_port = udp_sock.getsockname()[1]
    udp_sock.close()  # RTPStreamReceiver will re-bind the same port number

    local_ip = get_local_ip()
    logger.info(
        "Requesting stream for channel %s → UDP %s:%d",
        channel_number, local_ip, udp_port,
    )

    response = client.request_stream(channel_number, local_ip, udp_port)
    logger.info("Stream request response: %s", response)

    # Server may override the UDP port in its response
    server_udp_port = response.get("myAppUdpPort") or response.get("udpPort")
    if server_udp_port:
        try:
            udp_port = int(server_udp_port)
            logger.info("Using server-assigned UDP port: %d", udp_port)
        except (ValueError, TypeError):
            pass

    # Last-resort fallback: use the port embedded in the channel listing
    if not response and ch.get("port"):
        udp_port = ch["port"]
        logger.info("Falling back to channel listing port: %d", udp_port)

    receiver = RTPStreamReceiver(udp_port=udp_port, on_pcm=srv.feed_pcm)
    receiver.start()

    with _state_lock:
        _rtp_receivers[channel_number] = receiver

    return {"ok": True, "udp_port": udp_port}


def _stop_channel(channel_number: str) -> None:
    with _state_lock:
        recv   = _rtp_receivers.pop(channel_number, None)
        client = _api_clients.get(channel_number)
    if recv:
        recv.stop()
    if client:
        try:
            client.stop_stream(channel_number)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Channel polling (keep channel list fresh)
# ---------------------------------------------------------------------------

def _poll_channels_loop() -> None:
    """Background thread: re-fetch channel lists every 30 seconds."""
    while True:
        time.sleep(30)
        with _state_lock:
            servers_snapshot = dict(_servers)

        for name, srv_info in servers_snapshot.items():
            client = ListenWifiClient(srv_info["base_url"])
            try:
                channels = client.get_channels()
            except Exception:
                continue

            to_start: list[ChannelStreamServer] = []
            changed = False

            with _state_lock:
                for ch in channels:
                    num = ch["number"]
                    if num not in _channels:
                        _channels[num] = {
                            **ch,
                            "server_name": name,
                            "stream_port": 0,
                            "stream_url":  "",
                        }
                        _api_clients[num] = client
                        changed = True

                if changed:
                    _recompute_all_ports_locked()
                    for num, ch in _channels.items():
                        new_port = ch["stream_port"]
                        if _stream_servers.get(num) is None:
                            srv = ChannelStreamServer(new_port, num, ch["title"])
                            _stream_servers[num] = srv
                            to_start.append(srv)

            for srv in to_start:
                try:
                    srv.start()
                except Exception as exc:
                    logger.error("Poll: stream server start error: %s", exc)

            if changed:
                _emit_state()


# ---------------------------------------------------------------------------
# Flask routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/state")
def api_state():
    return jsonify(_build_state())


# ---------------------------------------------------------------------------
# SocketIO events
# ---------------------------------------------------------------------------

@socketio.on("connect")
def handle_connect():
    logger.debug("Browser connected")
    emit("state_update", _build_state())


@socketio.on("start_channel")
def handle_start_channel(data):
    channel_number = data.get("channel_number", "")
    logger.info("SocketIO: start_channel %s", channel_number)
    result = _start_channel(channel_number)
    _emit_state()
    emit("channel_action_result", {**result, "channel_number": channel_number})


@socketio.on("stop_channel")
def handle_stop_channel(data):
    channel_number = data.get("channel_number", "")
    logger.info("SocketIO: stop_channel %s", channel_number)
    _stop_channel(channel_number)
    _emit_state()
    emit("channel_action_result", {"ok": True, "channel_number": channel_number})


@socketio.on("refresh")
def handle_refresh(_data=None):
    emit("state_update", _build_state())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    discovery = ListenWifiDiscovery(
        on_server_added=_on_server_added,
        on_server_removed=_on_server_removed,
    )
    discovery.start()

    threading.Thread(
        target=_poll_channels_loop,
        name="channel-poller",
        daemon=True,
    ).start()

    logger.info("=" * 60)
    logger.info("ListenWifi Monitor starting")
    logger.info("  Dashboard:    http://localhost:%d", WEB_PORT)
    logger.info("  Port order:   lowest server IP → port %d, ascending", STREAM_BASE)
    logger.info("  Scanning for _exxothermic._tcp.local. …")
    logger.info("=" * 60)

    try:
        socketio.run(
            app, host="0.0.0.0", port=WEB_PORT, debug=False, use_reloader=False
        )
    finally:
        discovery.stop()
