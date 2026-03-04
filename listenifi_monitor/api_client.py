"""
api_client.py — REST API wrapper for the ListenWifi (Exxothermic) server.

Supports V2 API (/exxtractor/api/v2/) with automatic fallback to V1 (/api/myapp/).
No authentication is attempted (public/open channels).

Key findings from SDK binary analysis (PlaybackRetrofitAPI.class,
AudioStreamMixInAnnotations.class, PlaybackMixInAnnotations.class):

  • V2 stream path is  /exxtractor/api/v2/stream  (SINGULAR — not "streams")
  • The POST body must be nested:
        { "audioStream": { "channelNum": ..., "myAppIpAddress": ...,
                           "myAppUdpPort": ..., "deviceInformation": {...} } }
  • Stop stream:  DELETE /exxtractor/api/v2/stream?session=<client_ip>
  • V1 legacy:    POST/DELETE /api/myapp/channels (unchanged)
"""

import logging
import platform
import re
import uuid

import requests

logger = logging.getLogger(__name__)

# Stable device ID for the lifetime of this process
DEVICE_ID = str(uuid.uuid4())

# API path constants — confirmed from Android SDK PlaybackRetrofitAPI.class binary
V2_CHANNELS  = "/exxtractor/api/v2/networkChannels"
V2_STREAM    = "/exxtractor/api/v2/stream"   # SINGULAR — confirmed from binary decompile
V1_CHANNELS  = "/api/myapp/asClientChannels"
V1_STREAM    = "/api/myapp/channels"

REQUEST_TIMEOUT   = 5   # seconds — channel listing
STREAM_TIMEOUT    = 3   # seconds — stream start/stop requests
REDIRECT_TIMEOUT  = 1   # seconds — redirect-follow attempts (port 8000); fail fast

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


def _device_information() -> dict:
    """
    Build the deviceInformation object required by the V2 stream request.

    From AudioStreamMixInAnnotations.class (Android SDK):
        getIpAddress()               → "myAppIpAddress"
        getChannelNumber()           → "channelNum"
        getUdpPort()                 → "myAppUdpPort"
        getCurrentDeviceInformation()→ "deviceInformation"
            DeviceInformation fields: manufacturer, buildFingerprint, deviceId
    """
    return {
        "manufacturer":     platform.system() or "monitor",
        "buildFingerprint": platform.node()   or "monitor",
        "deviceId":         DEVICE_ID,
    }


def _safe_json(resp) -> dict:
    """Parse response JSON; return {} if body is empty or not valid JSON."""
    if not resp.content:
        return {}
    try:
        return resp.json()
    except ValueError:
        return {}


def _extract_html_redirect_url(text: str) -> str:
    """
    Extract the first href from an HTML 'moved to <a href="...">'-style body.
    Returns the URL string, or "" if not found.
    """
    m = re.search(r'href=["\']([^"\']+)["\']', text, re.IGNORECASE)
    return m.group(1) if m else ""


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

    def stop_stream(self, channel_number: str, client_ip: str = "") -> None:
        """
        Tell the server to stop sending RTP audio for this channel.

        V2 DELETE uses ?session=<client_ip> (confirmed from stopChannelPlaybackv2
        in PlaybackRetrofitAPI.class).  Falls back to ?channelNum= and V1.
        """
        v2_url = self.base_url + V2_STREAM
        v1_url = self.base_url + V1_STREAM

        # V2 preferred: session-based DELETE (client_ip is the session identifier)
        if client_ip:
            try:
                self._session.delete(
                    v2_url,
                    params={"session": client_ip},
                    timeout=STREAM_TIMEOUT,
                    allow_redirects=False,
                )
                logger.debug("stop_stream V2 session=%s", client_ip)
            except Exception as exc:
                logger.debug("stop_stream V2 session %s → %s", v2_url, exc)

        # V2 fallback: channelNum-based DELETE
        try:
            self._session.delete(
                v2_url,
                params={"channelNum": channel_number},
                timeout=STREAM_TIMEOUT,
                allow_redirects=False,
            )
        except Exception as exc:
            logger.debug("stop_stream V2 channelNum %s → %s", v2_url, exc)

        # V1 legacy
        try:
            self._session.delete(
                v1_url,
                params={"channelNum": channel_number},
                timeout=STREAM_TIMEOUT,
                allow_redirects=False,
            )
        except Exception as exc:
            logger.debug("stop_stream V1 %s → %s", v1_url, exc)

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
        """
        POST /exxtractor/api/v2/stream with the nested audioStream body structure
        confirmed from the Android SDK Jackson mixin annotations:

            AudioStreamMixInAnnotations:
                getIpAddress()                → "myAppIpAddress"
                getChannelNumber()            → "channelNum"
                getUdpPort()                  → "myAppUdpPort"
                getCurrentDeviceInformation() → "deviceInformation"

            PlaybackMixInAnnotations:
                mAudioStream                  → "audioStream"   (wraps the above)
        """
        url = self.base_url + V2_STREAM
        ch_int = int(channel_number) if str(channel_number).isdigit() else channel_number

        # Correct nested body structure (from SDK binary analysis)
        audio_stream = {
            "channelNum":      ch_int,
            "myAppIpAddress":  client_ip,
            "myAppUdpPort":    client_udp_port,
            "deviceInformation": _device_information(),
        }
        nested_body = {"audioStream": audio_stream}

        # Flat body fallback — older server versions may not require the wrapper
        flat_body = {
            "channelNum":     ch_int,
            "myAppIpAddress": client_ip,
            "myAppUdpPort":   client_udp_port,
        }

        attempts = [
            ("POST", nested_body),                                    # correct SDK format
            ("POST", flat_body),                                      # older server fallback
            ("GET",  flat_body),                                      # some servers use GET
            ("POST", {**flat_body, "channelNum": channel_number}),   # string channelNum
        ]

        last_status = None
        for method, body in attempts:
            try:
                if method == "POST":
                    resp = self._session.post(
                        url, json=body, timeout=STREAM_TIMEOUT, allow_redirects=False,
                    )
                else:
                    resp = self._session.get(
                        url, params=body, timeout=STREAM_TIMEOUT, allow_redirects=False,
                    )
                last_status = resp.status_code
                if resp.ok:
                    desc = "nested" if body is nested_body else "flat"
                    logger.info("V2 stream OK (%s %s channelNum=%s)",
                                method, desc, body.get("channelNum", body.get("audioStream", {}).get("channelNum")))
                    return _safe_json(resp)
                if resp.is_redirect:
                    location = resp.headers.get("Location", "")
                    logger.info("V2 stream redirect → %s", location)
                    return self._follow_stream_redirect(location, flat_body)
                logger.debug("V2 stream %s [%s] → HTTP %d %s",
                             url, method, resp.status_code, resp.reason)
            except Exception as exc:
                logger.debug("V2 stream %s [%s] → %s", url, method, exc)

        logger.warning("V2 stream %s — all attempts failed (last HTTP %s)", url, last_status)
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
                allow_redirects=False,  # server may redirect to port 8000
            )
            if resp.ok:
                result = _safe_json(resp)
                if result:
                    logger.info("V1 stream JSON OK")
                    return result
                # Non-JSON 200: check for "moved to <a href=...>" HTML redirect body
                redirect_url = _extract_html_redirect_url(resp.text)
                if redirect_url:
                    logger.info("V1 stream HTML body redirect → %s", redirect_url)
                    return self._follow_stream_redirect(redirect_url, body)
                logger.info("V1 stream OK (empty/non-JSON body — server may already be streaming)")
                return {}
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

        The V1 endpoint sometimes returns an HTML body pointing to port 8000.
        Port 8000 may not be reachable from management networks; if all attempts
        time out and V1 POST returned 200 the server may already be streaming.
        """
        if not location:
            return None
        attempts = [
            ("GET",  None),    # URL may already carry dummyBody query params
            ("POST", "json"),
            ("GET",  "params"),
        ]
        for method, body_style in attempts:
            try:
                if method == "GET" and body_style is None:
                    resp = self._session.get(
                        location, timeout=REDIRECT_TIMEOUT, allow_redirects=False,
                    )
                elif method == "POST":
                    resp = self._session.post(
                        location, json=body,
                        timeout=REDIRECT_TIMEOUT, allow_redirects=False,
                    )
                else:
                    resp = self._session.get(
                        location, params=body,
                        timeout=REDIRECT_TIMEOUT, allow_redirects=False,
                    )
                if resp.ok:
                    label = f"{method} as-is" if body_style is None else f"{method}+{body_style}"
                    logger.info("Stream redirect %s succeeded (%s)", location, label)
                    return _safe_json(resp) or {}
                logger.warning(
                    "Stream redirect %s [%s] → HTTP %d %s | %.200s",
                    location, method, resp.status_code, resp.reason, resp.text,
                )
            except Exception as exc:
                logger.debug("Stream redirect %s [%s] → %s", location, method, exc)

        logger.warning(
            "Stream redirect %s unreachable — if V1 POST returned 200 the server "
            "may still be sending RTP (check firewall / routing from 172.16.0.x to client)",
            location,
        )
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
