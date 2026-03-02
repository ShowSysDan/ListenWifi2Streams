"""
api_client.py — REST API wrapper for the ListenWifi (Exxothermic) server.

Supports V2 API (/exxtractor/api/v2/) with automatic fallback to V1 (/api/myapp/).
No authentication is attempted (public/open channels).
"""

import logging
import uuid

import requests

logger = logging.getLogger(__name__)

# Stable device ID for the lifetime of this process
DEVICE_ID = str(uuid.uuid4())

# API path constants (from iOS SDK EAEExxtractorAPIConstants.h + observed redirects)
V2_CHANNELS  = "/exxtractor/api/v2/networkChannels"
V2_STREAM    = "/exxtractor/api/v2/streams"   # plural — confirmed by V1 redirect
V1_CHANNELS  = "/api/myapp/asClientChannels"
V1_STREAM    = "/api/myapp/channels"

REQUEST_TIMEOUT = 5   # seconds — channel listing
STREAM_TIMEOUT  = 3   # seconds — stream start/stop requests (should be fast)

# Candidate paths tried by probe_server() for diagnostics
PROBE_PATHS = [
    V2_CHANNELS,
    V1_CHANNELS,
    "/exxtractor/api/v2/channels",
    "/api/channels",
    "/api/v1/channels",
    "/api/v2/channels",
    "/channels",
    "/",
]


class ListenWifiClient:
    """HTTP REST client for a single discovered ListenWifi server."""

    def __init__(self, base_url: str):
        # base_url e.g. "http://192.168.1.50:80"
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_channels(self) -> list[dict]:
        """
        Fetch the list of available audio channels from the server.

        Returns a list of normalised channel dicts.
        """
        channels = self._get_v2_channels()
        if channels is None:
            channels = self._get_v1_channels()
        return channels or []

    def request_stream(
        self,
        channel_number: str,
        client_ip: str,
        client_udp_port: int,
    ) -> dict:
        """
        Ask the server to start sending RTP audio to client_ip:client_udp_port.

        Returns the parsed response dict (may be empty on failure).
        """
        result = self._post_v2_stream(channel_number, client_ip, client_udp_port)
        if result is None:
            result = self._post_v1_stream(channel_number, client_ip, client_udp_port)
        return result or {}

    def stop_stream(self, channel_number: str) -> None:
        """Tell the server to stop sending RTP audio for this channel."""
        for url in (self.base_url + V2_STREAM, self.base_url + V1_STREAM):
            try:
                self._session.delete(
                    url,
                    params={"channelNum": channel_number},
                    timeout=STREAM_TIMEOUT,
                    allow_redirects=False,
                )
            except Exception as exc:
                logger.debug("stop_stream %s → %s", url, exc)

    # ------------------------------------------------------------------
    # V2 helpers
    # ------------------------------------------------------------------

    def _get_v2_channels(self) -> list[dict] | None:
        url = self.base_url + V2_CHANNELS
        try:
            resp = self._session.get(url, timeout=REQUEST_TIMEOUT)
            if not resp.ok:
                logger.warning(
                    "V2 channels %s → HTTP %d %s | %.300s",
                    url, resp.status_code, resp.reason, resp.text,
                )
                return None
            data = resp.json()
            # Response is a JSON array directly
            if isinstance(data, list):
                return [_normalize_channel(ch) for ch in data]
            # Or wrapped in a key
            if isinstance(data, dict):
                for key in ("channels", "networkChannels", "channelInfo", "data"):
                    if key in data and isinstance(data[key], list):
                        return [_normalize_channel(ch) for ch in data[key]]
            logger.warning(
                "V2 channels %s → unexpected shape %s | %.300s",
                url, type(data).__name__, str(data),
            )
            return None
        except Exception as exc:
            logger.warning("V2 channels %s → %s", url, exc)
            return None

    def _get_v1_channels(self) -> list[dict] | None:
        url = self.base_url + V1_CHANNELS
        try:
            resp = self._session.get(url, timeout=REQUEST_TIMEOUT)
            if not resp.ok:
                logger.warning(
                    "V1 channels %s → HTTP %d %s | %.300s",
                    url, resp.status_code, resp.reason, resp.text,
                )
                return None
            data = resp.json()
            # V1 wraps in {"channelInfo": [...]} or similar
            if isinstance(data, dict):
                for key in ("channelInfo", "channels", "networkChannels", "data"):
                    if key in data and isinstance(data[key], list):
                        return [_normalize_channel(ch) for ch in data[key]]
                logger.warning(
                    "V1 channels %s → unexpected dict shape, keys: %s",
                    url, list(data.keys()),
                )
                return None
            if isinstance(data, list):
                return [_normalize_channel(ch) for ch in data]
            return None
        except Exception as exc:
            logger.warning("V1 channels %s → %s", url, exc)
            return None

    # ------------------------------------------------------------------
    # Stream request helpers
    # ------------------------------------------------------------------

    def _post_v2_stream(
        self,
        channel_number: str,
        client_ip: str,
        client_udp_port: int,
    ) -> dict | None:
        # Body confirmed by inspecting V1 redirect: no deviceId
        body = {
            "channelNum":      channel_number,
            "myAppIpAddress":  client_ip,
            "myAppUdpPort":    client_udp_port,
        }
        url = self.base_url + V2_STREAM
        try:
            resp = self._session.post(
                url, json=body,
                timeout=STREAM_TIMEOUT,
                allow_redirects=False,
            )
            if resp.ok:
                return resp.json() if resp.content else {}
            if resp.is_redirect:
                location = resp.headers.get("Location", "")
                logger.info("V2 stream redirect → %s", location)
                return self._follow_stream_redirect(location, body)
            logger.warning(
                "V2 stream %s → HTTP %d %s | %.300s",
                url, resp.status_code, resp.reason, resp.text,
            )
        except Exception as exc:
            logger.warning("V2 stream %s → %s", url, exc)
        return None

    def _post_v1_stream(
        self,
        channel_number: str,
        client_ip: str,
        client_udp_port: int,
    ) -> dict | None:
        body = {
            "channelNum":     channel_number,
            "myAppIpAddress": client_ip,
            "myAppUdpPort":   client_udp_port,
        }
        url = self.base_url + V1_STREAM
        try:
            resp = self._session.post(
                url, json=body,
                timeout=STREAM_TIMEOUT,
                allow_redirects=False,  # server redirects to port 8000 which may be unreachable
            )
            if resp.ok:
                return resp.json() if resp.content else {}
            if resp.is_redirect:
                location = resp.headers.get("Location", "")
                logger.info("V1 stream redirect → %s", location)
                return self._follow_stream_redirect(location, body)
            logger.warning(
                "V1 stream %s → HTTP %d %s | %.300s",
                url, resp.status_code, resp.reason, resp.text,
            )
        except Exception as exc:
            logger.warning("V1 stream %s → %s", url, exc)
        return None

    def _follow_stream_redirect(self, location: str, body: dict) -> dict | None:
        """
        Attempt to follow a stream redirect to an alternate port/path.
        Tries POST first, then GET with params (servers sometimes use a
        dummyMethod=POST+dummyBody query-string pattern).
        """
        if not location:
            return None
        for attempt in ("post", "get"):
            try:
                if attempt == "post":
                    resp = self._session.post(
                        location, json=body,
                        timeout=STREAM_TIMEOUT, allow_redirects=False,
                    )
                else:
                    resp = self._session.get(
                        location, params=body,
                        timeout=STREAM_TIMEOUT, allow_redirects=False,
                    )
                if resp.ok:
                    logger.info("Stream redirect %s succeeded (%s)", location, attempt.upper())
                    return resp.json() if resp.content else {}
                logger.warning(
                    "Stream redirect %s [%s] → HTTP %d %s | %.200s",
                    location, attempt.upper(), resp.status_code, resp.reason, resp.text,
                )
            except Exception as exc:
                logger.warning("Stream redirect %s [%s] → %s", location, attempt.upper(), exc)
        return None


# ------------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------------

def probe_server(host: str, port: int = 80) -> list[dict]:
    """
    Hit every candidate API path on host:port and return raw results.
    Used by the /api/probe endpoint for debugging unknown server APIs.
    """
    base = f"http://{host}:{port}"
    sess = requests.Session()
    sess.headers["Accept"] = "application/json"
    results = []
    for path in PROBE_PATHS:
        url = base + path
        try:
            resp = sess.get(url, timeout=5, allow_redirects=True)
            results.append({
                "path":         path,
                "status":       resp.status_code,
                "reason":       resp.reason,
                "content_type": resp.headers.get("Content-Type", ""),
                "body":         resp.text[:1200],
            })
        except Exception as exc:
            results.append({
                "path":  path,
                "status": None,
                "error": str(exc),
            })
    return results


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _normalize_channel(raw: dict) -> dict:
    """
    Normalise a raw channel dict from either API version into a consistent schema.

    V2 field names (networkChannels endpoint):
        number, title, port (hardware path string), isPA, isPrivate,
        isAvailable, ipAddress, backgroundColor, apiVersion

    V1 field names (asClientChannels endpoint, wrapped in "channelInfo"):
        channelNum, channelLabel, gain, delay, backgroundColor, id,
        apiVersion, codecParams, rmsVoltage, port (hardware path string),
        enable, ipAddress, isPrivate, isPAChannel, currentSessions
    """
    # Channel number — V2: "number", V1: "channelNum" / "id"
    number = (
        raw.get("number")
        or raw.get("channelNum")
        or raw.get("exxtractorUniqueIdentifier")
        or raw.get("id")
        or ""
    )

    # Title — V2: "title", V1: "channelLabel"
    title = raw.get("title") or raw.get("channelLabel") or raw.get("name") or "Channel"

    # Available — V2: "isAvailable", V1: "enable"
    available = raw.get("isAvailable")
    if available is None:
        available = raw.get("enable", True)

    # PA channel — V2: "isPA", V1: "isPAChannel"
    is_pa = bool(raw.get("isPA") or raw.get("isPAChannel") or raw.get("isPa") or False)

    # port in the channel listing is a hardware device path, NOT a UDP port
    hw_port = str(raw.get("port") or "")

    return {
        "number":          str(number),
        "title":           title,
        "subtitle":        raw.get("subtitle") or "",
        "description":     raw.get("description") or "",
        "tag":             raw.get("tag") or "",
        "ipAddress":       raw.get("ipAddress") or "",
        "hw_port":         hw_port,             # hardware device path, e.g. "platform-xhci-hcd…"
        "isPA":            is_pa,
        "isPrivate":       bool(raw.get("isPrivate") or False),
        "isAvailable":     bool(available),
        "gain":            float(raw.get("gain") or 0.0),
        "apiVersion":      raw.get("apiVersion") or "v2",
        "codecParams":     raw.get("codecParams") or "",
        "rmsVoltage":      int(raw.get("rmsVoltage") or 0),
        "currentSessions": int(raw.get("currentSessions") or 0),
        "backgroundColor": str(raw.get("backgroundColor") or ""),
    }
