"""
api_client.py — REST API wrapper for the ListenWifi (Exxothermic) server.

Supports V2 API (/exxtractor/api/v2/) with automatic fallback to V1 (/api/myapp/).
No authentication is attempted (public/open channels).
"""

import logging
import uuid
from typing import Any

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


class ListenWifiClient:
    """HTTP REST client for a single discovered ListenWifi server."""

    def __init__(self, base_url: str):
        # base_url e.g. "http://192.168.1.50:80"
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        self._api_version: int = 2  # will fall back to 1 on first failure

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
            url = self.base_url + V2_STREAM
            self._session.delete(
                url,
                params={"deviceId": DEVICE_ID, "channelNum": channel_number},
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as exc:
            logger.debug("stop_stream V2 error: %s", exc)
        # Also attempt V1 stop (best-effort)
        try:
            url = self.base_url + V1_STREAM
            self._session.delete(
                url,
                params={"channelNum": channel_number},
                timeout=REQUEST_TIMEOUT,
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # V2 helpers
    # ------------------------------------------------------------------

    def _get_v2_channels(self) -> list[dict] | None:
        try:
            resp = self._session.get(
                self.base_url + V2_CHANNELS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            # Response may be a list directly or wrapped in a key
            if isinstance(data, list):
                return [_normalize_channel(ch) for ch in data]
            if isinstance(data, dict):
                for key in ("channels", "networkChannels", "data"):
                    if key in data and isinstance(data[key], list):
                        return [_normalize_channel(ch) for ch in data[key]]
            logger.warning("Unexpected V2 channel response shape: %s", type(data))
            return None
        except Exception as exc:
            logger.debug("V2 get_channels failed: %s", exc)
            return None

    def _get_v1_channels(self) -> list[dict] | None:
        try:
            resp = self._session.get(
                self.base_url + V1_CHANNELS,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            channels = data if isinstance(data, list) else data.get("channels", [])
            return [_normalize_channel(ch) for ch in channels]
        except Exception as exc:
            logger.debug("V1 get_channels failed: %s", exc)
            return None

    def _post_v2_stream(
        self,
        channel_number: str,
        client_ip: str,
        client_udp_port: int,
    ) -> dict | None:
        try:
            resp = self._session.post(
                self.base_url + V2_STREAM,
                json={
                    "deviceId": DEVICE_ID,
                    "channelNum": channel_number,
                    "myAppIpAddress": client_ip,
                    "myAppUdpPort": client_udp_port,
                },
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except Exception as exc:
            logger.debug("V2 request_stream failed: %s", exc)
            return None

    def _post_v1_stream(
        self,
        channel_number: str,
        client_ip: str,
        client_udp_port: int,
    ) -> dict | None:
        try:
            resp = self._session.post(
                self.base_url + V1_STREAM,
                json={
                    "channelNum": channel_number,
                    "myAppIpAddress": client_ip,
                    "myAppUdpPort": client_udp_port,
                },
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except Exception as exc:
            logger.debug("V1 request_stream failed: %s", exc)
            return None


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
