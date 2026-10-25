"""URL validation utilities for SSRF protection.

Provides :func:`validate_scan_url`, which ensures that only safe, publicly
reachable HTTP/HTTPS URLs are accepted for scanning.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


def _is_private_ip(ip: str) -> bool:
    """Return True if the IP address falls within a private or loopback range.

    Checked ranges:
    - Loopback:          127.0.0.0/8, ::1
    - Private (RFC1918): 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
    - Link-local:        169.254.0.0/16, fe80::/10
    - Unique local:      fc00::/7

    Args:
        ip: Dotted-decimal IPv4 or colon-separated IPv6 address string.

    Returns:
        ``True`` if the address is private/loopback, ``False`` otherwise.
    """
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return addr.is_private or addr.is_loopback or addr.is_link_local


def _resolve_host(host: str) -> str:
    """Resolve a hostname to its first IP address string.

    Args:
        host: Hostname or IP address string to resolve.

    Returns:
        The resolved IP address string.

    Raises:
        ValueError: If the hostname cannot be resolved.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise ValueError(f"Cannot resolve host '{host}': {exc}") from exc

    if not infos:
        raise ValueError(f"No address records found for host '{host}'")

    # infos is a list of (family, type, proto, canonname, sockaddr) tuples;
    # sockaddr is (ip, port) for IPv4 or (ip, port, flow, scope) for IPv6.
    return infos[0][4][0]


def validate_scan_url(url: str) -> str:
    """Validate that a URL is safe to scan.

    Rules:
    - Scheme must be ``http`` or ``https``.
    - Host must not resolve to a private, loopback, or link-local IP address
      (prevents SSRF attacks against internal infrastructure).

    Args:
        url: URL string to validate (already parsed by Pydantic ``HttpUrl``).

    Returns:
        The validated URL string, unchanged.

    Raises:
        ValueError: If the URL fails any validation rule.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Unsupported scheme '{parsed.scheme}'. Only http and https are allowed."
        )

    host = parsed.hostname
    if not host:
        raise ValueError("URL has no hostname.")

    resolved_ip = _resolve_host(host)

    if _is_private_ip(resolved_ip):
        raise ValueError(
            f"Host '{host}' resolves to a private/loopback IP ({resolved_ip}). "
            "Scanning internal addresses is not permitted."
        )

    return url
