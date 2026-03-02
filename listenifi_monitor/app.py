"""
app.py — ListenWifi Audio Stream Monitor
Flask web dashboard (port 6000) + per-channel MP3 relay (ports 6001+).

Usage:
    python app.py

Then open http://localhost:6000 to see the dashboard.
For each discovered channel, connect VLC to http://<your-ip>:<channel-port>/
"""

import logging
import socket
import threading
import time
from typing import Any

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
STREAM_BASE = 6001  # stream_port = STREAM_BASE + (channel_number - 1) for numeric IDs

# ---------------------------------------------------------------------------
# Global state  (all mutations must hold _state_lock)
# ---------------------------------------------------------------------------
_state_lock = threading.Lock()

# mDNS name → {"name", "host", "port", "base_url"}
_servers: dict[str, dict] = {}

# channel_number (str) → channel info dict (extended with our fields)
_channels: dict[str, dict] = {}

# channel_number → ChannelStreamServer
_stream_servers: dict[str, ChannelStreamServer] = {}

# channel_number → RTPStreamReceiver
_rtp_receivers: dict[str, RTPStreamReceiver] = {}

# channel_number → ListenWifiClient (the client for that channel's server)
_api_clients: dict[str, ListenWifiClient] = {}

# Non-integer channel IDs need sequential port allocation
_next_fallback_port: list[int] = [STREAM_BASE]


# ---------------------------------------------------------------------------
# Port assignment
# ---------------------------------------------------------------------------

def _assign_port(channel_number: str) -> int:
    """
    Derive a stable HTTP stream port for a channel.

    If channel_number is a positive integer N → port = STREAM_BASE + N - 1
    (so channel "1" → 6001, "12" → 6012).

    Otherwise (UUID / non-integer) → allocate the next sequential fallback port.
    """
    try:
        n = int(channel_number)
        if 1 <= n <= 999:
            return STREAM_BASE + n - 1
    except (ValueError, TypeError):
        pass
    # Fallback: sequential allocation
    port = _next_fallback_port[0]
    _next_fallback_port[0] += 1
    return port


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _local_ip() -> str:
    return get_local_ip()


def _build_state() -> dict:
    """Serialise current state for SocketIO broadcast."""
    with _state_lock:
        servers_list = list(_servers.values())
        channels_list = []
        for ch in _channels.values():
            num = ch["number"]
            recv = _rtp_receivers.get(num)
            srv  = _stream_servers.get(num)
            status = "idle"
            if recv and recv.is_running:
                status = "active" if recv.packets_received > 0 else "requesting"
            channels_list.append({
                **ch,
                "status":         status,
                "active_clients": srv.active_clients if srv else 0,
                "packets_in":     recv.packets_received if recv else 0,
            })
        # Sort by stream_port for consistent order
        channels_list.sort(key=lambda c: c.get("stream_port", 9999))
    return {"servers": servers_list, "channels": channels_list, "local_ip": _local_ip()}


def _emit_state() -> None:
    socketio.emit("state_update", _build_state())


# ---------------------------------------------------------------------------
# mDNS callbacks  (called from Zeroconf I/O thread)
# ---------------------------------------------------------------------------

def _on_server_added(server_info: dict) -> None:
    name = server_info["name"]
    logger.info("Server added: %s", name)

    client = ListenWifiClient(server_info["base_url"])
    channels = client.get_channels()
    logger.info("  → %d channel(s) from %s", len(channels), name)

    with _state_lock:
        _servers[name] = server_info

        for ch in channels:
            num = ch["number"]
            if num in _channels:
                continue  # already known

            port = _assign_port(num)
            stream_url = f"http://{_local_ip()}:{port}/"
            ch_extended = {
                **ch,
                "server_name": name,
                "stream_port": port,
                "stream_url":  stream_url,
            }
            _channels[num] = ch_extended
            _api_clients[num] = client

            # Create and start the HTTP stream server for this channel
            srv = ChannelStreamServer(port, num, ch["title"])
            try:
                srv.start()
                _stream_servers[num] = srv
            except Exception as exc:
                logger.error("Could not start stream server for channel %s: %s", num, exc)

    _emit_state()


def _on_server_removed(name: str) -> None:
    logger.info("Server removed: %s", name)
    with _state_lock:
        _servers.pop(name, None)
        # Stop streams associated with this server
        to_remove = [
            num for num, ch in _channels.items() if ch.get("server_name") == name
        ]
        for num in to_remove:
            _stop_channel_locked(num)
            _channels.pop(num, None)
            _api_clients.pop(num, None)
    _emit_state()


# ---------------------------------------------------------------------------
# Stream control  (internal; call with _state_lock if needed)
# ---------------------------------------------------------------------------

def _stop_channel_locked(channel_number: str) -> None:
    """Stop RTP receiver + notify API. Must be called with _state_lock held or on teardown."""
    recv = _rtp_receivers.pop(channel_number, None)
    if recv:
        recv.stop()
    srv = _stream_servers.pop(channel_number, None)
    if srv:
        srv.stop()
    client = _api_clients.get(channel_number)
    if client:
        try:
            client.stop_stream(channel_number)
        except Exception:
            pass


def _start_channel(channel_number: str) -> dict:
    """
    Start streaming a channel:
      1. Open a UDP socket on a free port.
      2. Ask the ListenWifi server to send RTP to our IP:port.
      3. Start an RTPStreamReceiver that feeds PCM into the ChannelStreamServer.
    """
    with _state_lock:
        ch = _channels.get(channel_number)
        client = _api_clients.get(channel_number)
        srv = _stream_servers.get(channel_number)

    if not ch or not client or not srv:
        return {"ok": False, "error": "Unknown channel"}

    # Stop any existing receiver first
    with _state_lock:
        old = _rtp_receivers.pop(channel_number, None)
    if old:
        old.stop()

    # Pick a free UDP port
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("0.0.0.0", 0))
    udp_port = udp_sock.getsockname()[1]
    udp_sock.close()  # RTPStreamReceiver will re-bind

    local_ip = _local_ip()
    logger.info(
        "Requesting stream for channel %s → UDP %s:%d", channel_number, local_ip, udp_port
    )

    # Ask server to send us RTP
    response = client.request_stream(channel_number, local_ip, udp_port)
    logger.info("Stream request response: %s", response)

    # If the server returned a different UDP port, use that instead
    server_udp_port = response.get("myAppUdpPort") or response.get("udpPort")
    if server_udp_port:
        try:
            udp_port = int(server_udp_port)
            logger.info("Using server-assigned UDP port: %d", udp_port)
        except (ValueError, TypeError):
            pass

    # Fallback: if REST request failed, try the port listed in the channel info
    if not response and ch.get("port"):
        udp_port = ch["port"]
        logger.info("Falling back to channel listing port: %d", udp_port)

    # Create and start receiver
    receiver = RTPStreamReceiver(
        udp_port=udp_port,
        on_pcm=srv.feed_pcm,
    )
    receiver.start()

    with _state_lock:
        _rtp_receivers[channel_number] = receiver

    return {"ok": True, "udp_port": udp_port}


def _stop_channel(channel_number: str) -> None:
    with _state_lock:
        recv = _rtp_receivers.pop(channel_number, None)
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
            known_numbers = set(_channels.keys())

        for name, srv_info in servers_snapshot.items():
            client = ListenWifiClient(srv_info["base_url"])
            try:
                channels = client.get_channels()
            except Exception:
                continue

            changed = False
            with _state_lock:
                for ch in channels:
                    num = ch["number"]
                    if num not in _channels:
                        port = _assign_port(num)
                        _channels[num] = {
                            **ch,
                            "server_name": name,
                            "stream_port": port,
                            "stream_url": f"http://{_local_ip()}:{port}/",
                        }
                        _api_clients[num] = client
                        srv = ChannelStreamServer(port, num, ch["title"])
                        try:
                            srv.start()
                            _stream_servers[num] = srv
                        except Exception as exc:
                            logger.error("Poll: stream server start error: %s", exc)
                        changed = True

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


@app.route("/demo")
def demo():
    """Inject mock data for UI testing without a live server."""
    mock_server = {
        "name": "mock._exxothermic._tcp.local.",
        "host": "192.168.1.50",
        "port": 80,
        "base_url": "http://192.168.1.50:80",
        "friendly_name": "Demo ListenWifi Unit",
    }
    mock_channels = [
        {
            "number": str(i), "title": f"Channel {i}", "subtitle": "",
            "description": "", "tag": "", "ipAddress": "192.168.1.50",
            "port": 5000 + i, "isPA": (i == 1), "isPrivate": False, "gain": 0.0,
            "apiVersion": "v2", "server_name": mock_server["name"],
            "stream_port": STREAM_BASE + i - 1,
            "stream_url": f"http://{_local_ip()}:{STREAM_BASE + i - 1}/",
        }
        for i in range(1, 13)
    ]
    with _state_lock:
        _servers[mock_server["name"]] = mock_server
        for ch in mock_channels:
            _channels[ch["number"]] = ch
    _emit_state()
    return jsonify({"ok": True, "message": "Mock data injected — refresh the dashboard."})


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
    # Start mDNS discovery
    discovery = ListenWifiDiscovery(
        on_server_added=_on_server_added,
        on_server_removed=_on_server_removed,
    )
    discovery.start()

    # Start channel polling thread
    threading.Thread(
        target=_poll_channels_loop,
        name="channel-poller",
        daemon=True,
    ).start()

    logger.info("=" * 60)
    logger.info("ListenWifi Monitor starting")
    logger.info("  Dashboard:    http://localhost:%d", WEB_PORT)
    logger.info("  Stream ports: %d – %d (one per channel)", STREAM_BASE, STREAM_BASE + 99)
    logger.info("  Scanning for _exxothermic._tcp.local. …")
    logger.info("=" * 60)

    try:
        socketio.run(app, host="0.0.0.0", port=WEB_PORT, debug=False, use_reloader=False)
    finally:
        discovery.stop()
