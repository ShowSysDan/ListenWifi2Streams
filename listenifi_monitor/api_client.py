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

# API path constants (from iOS SDK EAEExxtractorAPIConstants.h)
V2_CHANNELS  = "/exxtractor/api/v2/networkChannels"
V2_STREAM    = "/exxtractor/api/v2/stream"
V1_CHANNELS  = "/api/myapp/asClientChannels"
V1_STREAM    = "/api/myapp/channels"

REQUEST_TIMEOUT = 5  # seconds

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

        Returns a list of dicts with at minimum:
            number, title, subtitle, ipAddress, port, isPA, isPrivate, gain
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
        try:
            self._session.delete(
                self.base_url + V2_STREAM,
                params={"deviceId": DEVICE_ID, "channelNum": channel_number},
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as exc:
            logger.debug("stop_stream V2 error: %s", exc)
        try:
            self._session.delete(
                self.base_url + V1_STREAM,
                params={"channelNum": channel_number},
                timeout=REQUEST_TIMEOUT,
            )
        except Exception:
            pass

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
            if isinstance(data, list):
                return [_normalize_channel(ch) for ch in data]
            if isinstance(data, dict):
                for key in ("channels", "networkChannels", "data"):
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
            channels = data if isinstance(data, list) else data.get("channels", [])
            return [_normalize_channel(ch) for ch in channels]
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
        url = self.base_url + V2_STREAM
        try:
            resp = self._session.post(
                url,
                json={
                    "deviceId": DEVICE_ID,
                    "channelNum": channel_number,
                    "myAppIpAddress": client_ip,
                    "myAppUdpPort": client_udp_port,
                },
                timeout=REQUEST_TIMEOUT,
            )
            if not resp.ok:
                logger.warning(
                    "V2 stream %s → HTTP %d %s | %.300s",
                    url, resp.status_code, resp.reason, resp.text,
                )
                return None
            return resp.json() if resp.content else {}
        except Exception as exc:
            logger.warning("V2 stream %s → %s", url, exc)
            return None

    def _post_v1_stream(
        self,
        channel_number: str,
        client_ip: str,
        client_udp_port: int,
    ) -> dict | None:
        url = self.base_url + V1_STREAM
        try:
            resp = self._session.post(
                url,
                json={
                    "channelNum": channel_number,
                    "myAppIpAddress": client_ip,
                    "myAppUdpPort": client_udp_port,
                },
                timeout=REQUEST_TIMEOUT,
            )
            if not resp.ok:
                logger.warning(
                    "V1 stream %s → HTTP %d %s | %.300s",
                    url, resp.status_code, resp.reason, resp.text,
                )
                return None
            return resp.json() if resp.content else {}
        except Exception as exc:
            logger.warning("V1 stream %s → %s", url, exc)
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

    JSON field names come from API_V2_AudioChannelMapping.plist:
        number → exxtractorUniqueIdentifier
        title, subtitle, description, ipAddress, port,
        isPA, isPrivate, gain, tag, apiVersion, passphrase
    """
    return {
        "number":      str(raw.get("number") or raw.get("exxtractorUniqueIdentifier") or ""),
        "title":       raw.get("title") or raw.get("name") or "Channel",
        "subtitle":    raw.get("subtitle") or "",
        "description": raw.get("description") or "",
        "tag":         raw.get("tag") or "",
        "ipAddress":   raw.get("ipAddress") or "",
        "port":        int(raw.get("port") or 0),
        "isPA":        bool(raw.get("isPA") or raw.get("isPa") or False),
        "isPrivate":   bool(raw.get("isPrivate") or False),
        "gain":        float(raw.get("gain") or 0.0),
        "apiVersion":  raw.get("apiVersion") or "v2",
    }
