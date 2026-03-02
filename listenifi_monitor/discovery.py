"""
discovery.py — mDNS discovery for ListenWifi (Exxothermic) servers.

Scans the local network for _exxothermic._tcp.local. services published by
ListenWifi hardware (MyBox / ExXtractor units).
"""

import logging
import socket
import threading
from typing import Callable

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_exxothermic._tcp.local."


class ListenWifiDiscovery(ServiceListener):
    """
    Discovers ListenWifi servers via mDNS/Zeroconf.

    Callbacks are called from the Zeroconf I/O thread — keep them fast
    (hand off to another thread if you need to do network I/O).
    """

    def __init__(
        self,
        on_server_added: Callable[[dict], None],
        on_server_removed: Callable[[str], None],
    ):
        self._on_added = on_server_added
        self._on_removed = on_server_removed
        self._zeroconf: Zeroconf | None = None
        self._browser: ServiceBrowser | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start mDNS scanning (non-blocking; runs in background thread)."""
        with self._lock:
            if self._zeroconf is not None:
                return
            self._zeroconf = Zeroconf()
            self._browser = ServiceBrowser(self._zeroconf, SERVICE_TYPE, self)
            logger.info("mDNS discovery started for %s", SERVICE_TYPE)

    def stop(self) -> None:
        """Stop mDNS scanning and release resources."""
        with self._lock:
            if self._browser:
                self._browser.cancel()
                self._browser = None
            if self._zeroconf:
                self._zeroconf.close()
                self._zeroconf = None
            logger.info("mDNS discovery stopped")

    # ------------------------------------------------------------------
    # ServiceListener interface (called by Zeroconf I/O thread)
    # ------------------------------------------------------------------

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info is None:
            logger.warning("Could not resolve service info for %s", name)
            return

        addresses = info.parsed_scoped_addresses()
        # Prefer IPv4
        host = next(
            (a for a in addresses if ":" not in a),  # exclude IPv6
            addresses[0] if addresses else None,
        )
        if not host:
            logger.warning("No address found for %s", name)
            return

        port = info.port
        server_info = {
            "name": name,
            "host": host,
            "port": port,
            "base_url": f"http://{host}:{port}",
            "friendly_name": info.server or name,
        }
        logger.info("ListenWifi server found: %s at %s:%d", name, host, port)
        self._on_added(server_info)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        logger.info("ListenWifi server removed: %s", name)
        self._on_removed(name)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # Re-resolve and treat as a fresh add
        self.add_service(zc, type_, name)
