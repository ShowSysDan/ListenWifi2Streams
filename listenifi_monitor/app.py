"""
app.py — ListenWifi Audio Stream Monitor
Flask web dashboard (port 7000) + per-channel MP3 relay (ports 7001+).

Port assignment (IP-sorted):
  Channels are sorted by (server_ip_ascending, channel_number_ascending) and
  assigned ports 7001, 7002, … in that order.

  Example — 6 servers × 2 channels each:
    192.168.1.10  ch.1 → 7001
    192.168.1.10  ch.2 → 7002
    192.168.1.20  ch.1 → 7003
    192.168.1.20  ch.2 → 7004
    ...
    192.168.1.60  ch.2 → 7012

  If a new server is discovered that sorts lower than existing servers, all
  ports are recomputed and the affected stream servers are restarted.

Usage:
    python app.py
    open http://localhost:7000

VLC:
    vlc http://<your-ip>:<channel-port>/
"""

import json
import logging
import logging.handlers
import os
import socket
import threading
import time

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

from api_client import ListenWifiClient, probe_server
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
# Config defaults  (overridden by settings.json at startup)
# ---------------------------------------------------------------------------
SYSLOG_HOST: str     = ""
SYSLOG_PORT: int     = 514
SYSLOG_TCP:  bool    = False
STATIC_SERVERS: list = []

# ---------------------------------------------------------------------------
# Settings persistence
# ---------------------------------------------------------------------------
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

_syslog_handler: logging.Handler | None = None


def _load_settings() -> None:
    global STATIC_SERVERS, SYSLOG_HOST, SYSLOG_PORT, SYSLOG_TCP
    if not os.path.exists(SETTINGS_FILE):
        return
    try:
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
        STATIC_SERVERS = data.get("static_servers", STATIC_SERVERS)
        SYSLOG_HOST    = data.get("syslog_host",    SYSLOG_HOST)
        SYSLOG_PORT    = int(data.get("syslog_port", SYSLOG_PORT))
        SYSLOG_TCP     = bool(data.get("syslog_tcp",  SYSLOG_TCP))
        logger.info("Settings loaded from %s", SETTINGS_FILE)
    except Exception as exc:
        logger.warning("Could not load settings.json: %s", exc)


def _save_settings() -> None:
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump({
                "static_servers": STATIC_SERVERS,
                "syslog_host":    SYSLOG_HOST,
                "syslog_port":    SYSLOG_PORT,
                "syslog_tcp":     SYSLOG_TCP,
            }, f, indent=2)
    except Exception as exc:
        logger.warning("Could not save settings.json: %s", exc)


def _setup_syslog() -> None:
    """Install (or replace) the remote syslog handler based on current config."""
    global _syslog_handler
    root = logging.getLogger()
    if _syslog_handler is not None:
        root.removeHandler(_syslog_handler)
        _syslog_handler = None
    if not SYSLOG_HOST:
        return
    socktype = socket.SOCK_STREAM if SYSLOG_TCP else socket.SOCK_DGRAM
    try:
        handler = logging.handlers.SysLogHandler(
            address=(SYSLOG_HOST, SYSLOG_PORT),
            socktype=socktype,
        )
        handler.setFormatter(logging.Formatter(
            "listenifi: %(levelname)s %(name)s: %(message)s"
        ))
        root.addHandler(handler)
        _syslog_handler = handler
        logger.info(
            "Syslog forwarding → %s:%d (%s)",
            SYSLOG_HOST, SYSLOG_PORT, "TCP" if SYSLOG_TCP else "UDP",
        )
    except Exception as exc:
        logger.warning("Syslog setup failed: %s", exc)


_load_settings()
_setup_syslog()

# ---------------------------------------------------------------------------
# Flask + SocketIO
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "listenifi-monitor-secret"
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# ---------------------------------------------------------------------------
# Ports
# ---------------------------------------------------------------------------
WEB_PORT    = 7000
STREAM_BASE = 7001

# ---------------------------------------------------------------------------
# Global state  (all mutations must hold _state_lock)
# ---------------------------------------------------------------------------
_state_lock = threading.Lock()

# mDNS name → {"name", "host", "port", "base_url", "friendly_name"}
_servers: dict[str, dict] = {}

# uid (f"{server_host}:{channel_number}") → channel info dict (extended with our fields)
_channels: dict[str, dict] = {}

# uid → ChannelStreamServer
_stream_servers: dict[str, ChannelStreamServer] = {}

# uid → RTPStreamReceiver
_rtp_receivers: dict[str, RTPStreamReceiver] = {}

# uid → ListenWifiClient (the client for that channel's server)
_api_clients: dict[str, ListenWifiClient] = {}

# local_ip used when starting each channel's stream, needed for DELETE ?session=
_channel_ips: dict[str, str] = {}


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
    Assign stream ports 7001, 7002, … ordered by (server_ip_asc, channel_num_asc).

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
                uid  = ch["uid"]
                recv = _rtp_receivers.get(uid)
                ss   = _stream_servers.get(uid)
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
            uid = f"{server_info['host']}:{ch['number']}"
            if uid not in _channels:
                _channels[uid] = {
                    **ch,
                    "uid":         uid,
                    "server_name": name,
                    "stream_port": 0,
                    "stream_url":  "",
                }
                _api_clients[uid] = client

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

def _start_channel(uid: str) -> dict:
    """
    Start streaming a channel:
      1. Bind a free UDP port.
      2. Ask the ListenWifi server to unicast RTP to our IP:UDP port.
      3. RTPStreamReceiver feeds PCM into ChannelStreamServer → MP3 → VLC.
    """
    with _state_lock:
        ch     = _channels.get(uid)
        client = _api_clients.get(uid)
        srv    = _stream_servers.get(uid)

    if not ch or not client or not srv:
        return {"ok": False, "error": "Unknown channel"}

    # Stop any existing receiver for this channel
    with _state_lock:
        old = _rtp_receivers.pop(uid, None)
    if old:
        old.stop()

    # Let the OS pick a free UDP port
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("0.0.0.0", 0))
    udp_port = udp_sock.getsockname()[1]
    udp_sock.close()  # RTPStreamReceiver will re-bind the same port number

    server_host = uid.split(":")[0]   # e.g. "172.16.0.5"
    local_ip = get_local_ip(server_host)  # IP on the interface that routes to this server
    channel_number = ch["number"]   # raw API channel number (e.g. "1", "2")
    logger.info(
        "Requesting stream for channel %s [%s] → UDP %s:%d (local iface for %s)",
        uid, channel_number, local_ip, udp_port, server_host,
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

    receiver = RTPStreamReceiver(udp_port=udp_port, on_pcm=srv.feed_pcm)
    receiver.start()

    with _state_lock:
        _rtp_receivers[uid] = receiver
        _channel_ips[uid]   = local_ip

    return {"ok": True, "udp_port": udp_port}


def _stop_channel(uid: str) -> None:
    with _state_lock:
        recv      = _rtp_receivers.pop(uid, None)
        client    = _api_clients.get(uid)
        ch        = _channels.get(uid)
        local_ip  = _channel_ips.pop(uid, "")
    if recv:
        recv.stop()
    if client and ch:
        try:
            client.stop_stream(ch["number"], client_ip=local_ip)
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
                    uid = f"{srv_info['host']}:{ch['number']}"
                    if uid not in _channels:
                        _channels[uid] = {
                            **ch,
                            "uid":         uid,
                            "server_name": name,
                            "stream_port": 0,
                            "stream_url":  "",
                        }
                        _api_clients[uid] = client
                        changed = True

                if changed:
                    _recompute_all_ports_locked()
                    for uid, ch in _channels.items():
                        new_port = ch["stream_port"]
                        if _stream_servers.get(uid) is None:
                            srv = ChannelStreamServer(new_port, uid, ch["title"])
                            _stream_servers[uid] = srv
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


@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify({
        "static_servers": STATIC_SERVERS,
        "syslog_host":    SYSLOG_HOST,
        "syslog_port":    SYSLOG_PORT,
        "syslog_tcp":     SYSLOG_TCP,
    })


@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    global STATIC_SERVERS, SYSLOG_HOST, SYSLOG_PORT, SYSLOG_TCP
    data = request.get_json(force=True, silent=True) or {}

    new_servers     = [str(s).strip() for s in data.get("static_servers", []) if str(s).strip()]
    new_syslog_host = str(data.get("syslog_host", "")).strip()
    new_syslog_port = int(data.get("syslog_port", 514))
    new_syslog_tcp  = bool(data.get("syslog_tcp", False))

    # Diff static servers and apply changes
    old_set = set(STATIC_SERVERS)
    new_set = set(new_servers)
    for entry in (new_set - old_set):
        _probe_static_entry(entry)
    for entry in (old_set - new_set):
        host = entry.strip().rsplit(":", 1)[0] if ":" in entry else entry.strip()
        _on_server_removed(f"static-{host}")

    STATIC_SERVERS = new_servers
    SYSLOG_HOST    = new_syslog_host
    SYSLOG_PORT    = new_syslog_port
    SYSLOG_TCP     = new_syslog_tcp
    _setup_syslog()
    _save_settings()
    logger.info("Settings saved via UI")
    return jsonify({"ok": True})


@app.route("/api/probe")
def api_probe():
    """Diagnostic: hit candidate API paths on a server and return raw results."""
    host = request.args.get("host", "").strip()
    try:
        port = int(request.args.get("port", 80))
    except ValueError:
        return jsonify({"error": "invalid port"}), 400
    if not host:
        return jsonify({"error": "host required"}), 400
    results = probe_server(host, port)
    return jsonify({"host": host, "port": port, "results": results})


# ---------------------------------------------------------------------------
# SocketIO events
# ---------------------------------------------------------------------------

@socketio.on("connect")
def handle_connect():
    logger.debug("Browser connected")
    emit("state_update", _build_state())


@socketio.on("start_channel")
def handle_start_channel(data):
    uid = data.get("uid", "")
    logger.info("SocketIO: start_channel %s", uid)
    result = _start_channel(uid)
    _emit_state()
    emit("channel_action_result", {**result, "uid": uid})


@socketio.on("stop_channel")
def handle_stop_channel(data):
    uid = data.get("uid", "")
    logger.info("SocketIO: stop_channel %s", uid)
    _stop_channel(uid)
    _emit_state()
    emit("channel_action_result", {"ok": True, "uid": uid})


@socketio.on("refresh")
def handle_refresh(_data=None):
    emit("state_update", _build_state())


# ---------------------------------------------------------------------------
# Static server probing
# ---------------------------------------------------------------------------

def _probe_static_entry(entry: str) -> None:
    """Parse and probe one 'host' or 'host:port' static server entry."""
    entry = entry.strip()
    if not entry:
        return
    if ":" in entry:
        host, port_str = entry.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            logger.warning("Static server: invalid entry %r (bad port)", entry)
            return
    else:
        host, port = entry, 80
    server_info = {
        "name":          f"static-{host}",
        "host":          host,
        "port":          port,
        "base_url":      f"http://{host}:{port}",
        "friendly_name": host,
    }
    logger.info("Static server: probing %s:%d", host, port)
    threading.Thread(
        target=_on_server_added,
        args=(server_info,),
        name=f"static-probe-{host}",
        daemon=True,
    ).start()


def _probe_static_servers() -> None:
    for entry in STATIC_SERVERS:
        _probe_static_entry(entry)


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

    if STATIC_SERVERS:
        _probe_static_servers()

    logger.info("=" * 60)
    logger.info("ListenWifi Monitor starting")
    logger.info("  Dashboard:    http://localhost:%d", WEB_PORT)
    logger.info("  Port order:   lowest server IP → port %d, ascending", STREAM_BASE)
    logger.info("  Scanning for _exxothermic._tcp.local. …")
    if STATIC_SERVERS:
        logger.info("  Static servers: %s", ", ".join(STATIC_SERVERS))
    if SYSLOG_HOST:
        logger.info("  Syslog:         %s:%d (%s)", SYSLOG_HOST, SYSLOG_PORT, "TCP" if SYSLOG_TCP else "UDP")
    logger.info("=" * 60)

    try:
        socketio.run(
            app, host="0.0.0.0", port=WEB_PORT, debug=False, use_reloader=False
        )
    finally:
        discovery.stop()
