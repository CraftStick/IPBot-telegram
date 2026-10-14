"""Domain registration data (registrar and dates) via RDAP, with a classic WHOIS fallback.

RDAP is the modern JSON replacement of WHOIS, but many ccTLDs (.ru, .рф, .io, .de...)
don't support it yet, so for them the plain-text WHOIS protocol (TCP port 43) is used.
"""

import functools
import logging
import re
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

RDAP_BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
IANA_WHOIS_SERVER = "whois.iana.org"
TIMEOUT = 4
CACHE_TTL = 3600  # seconds; registration data rarely changes
CACHE_MAX_SIZE = 1000
MAX_WHOIS_RESPONSE = 100_000  # bytes
MAX_LEVELS = 4  # a.b.example.co.uk -> try at most the last 4 labels
SERVER_RETRY_AFTER = 600  # seconds to skip a WHOIS server that didn't answer

# Used when the registry's own server is unreachable (whois.tcinet.ru doesn't answer
# from some networks). RU-CENTER only knows domains registered through it.
WHOIS_FALLBACK_SERVERS = {
    "ru": ("whois.nic.ru",),
    "su": ("whois.nic.ru",),
    "xn--p1ai": ("whois.nic.ru",),  # .рф
}

# WHOIS servers name the same fields differently
WHOIS_FIELDS = {
    "registrar": ("registrar", "sponsoring registrar", "registrar name"),
    "created": (
        "creation date", "created", "created on", "registered on", "registered",
        "registration time", "domain registration date",
    ),
    "expires": (
        "registry expiry date", "registrar registration expiration date", "expiry date",
        "expiration date", "expiration time", "expires", "expires on", "paid-till", "renewal date",
    ),
}

DATE_FORMATS = ("%Y-%m-%d", "%d-%b-%Y", "%Y.%m.%d", "%d.%m.%Y", "%Y/%m/%d", "%d/%m/%Y")

log = logging.getLogger("ipbot.domaininfo")


@dataclass
class DomainInfo:
    domain: str
    registrar: str | None = None
    created: datetime | None = None
    expires: datetime | None = None


def parse_date(value):
    """Parse the many date formats used by registries into an aware UTC datetime."""
    if not value:
        return None
    value = value.strip()
    candidates = [value, value.split()[0], value[:10]]

    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
            for fmt in DATE_FORMATS:
                try:
                    parsed = datetime.strptime(candidate, fmt)
                    break
                except ValueError:
                    pass
        if parsed:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


# ---------- RDAP ----------

_rdap_servers = None  # tld -> RDAP base URL


def rdap_servers():
    """TLD -> RDAP server map from the IANA bootstrap registry (loaded once)."""
    global _rdap_servers
    if _rdap_servers is None:
        try:
            response = requests.get(RDAP_BOOTSTRAP_URL, timeout=TIMEOUT)
            response.raise_for_status()
            servers = {}
            for tlds, urls in response.json()["services"]:
                url = next((u for u in urls if u.startswith("https://")), urls[0])
                for tld in tlds:
                    servers[tld.lower()] = url.rstrip("/") + "/"
            _rdap_servers = servers
        except (requests.RequestException, ValueError, KeyError) as e:
            log.warning("Could not load the RDAP bootstrap registry: %s", e)
            return {}  # try again next time
    return _rdap_servers


def parse_rdap(data, domain):
    events = {e.get("eventAction"): e.get("eventDate") for e in data.get("events", [])}

    registrar = None
    for entity in data.get("entities", []):
        if "registrar" in entity.get("roles", []):
            vcard = entity.get("vcardArray", [None, []])[1]
            registrar = next((item[3] for item in vcard if item[0] == "fn"), None)
            break

    return DomainInfo(
        domain=(data.get("ldhName") or domain).lower(),
        registrar=registrar,
        created=parse_date(events.get("registration")),
        expires=parse_date(events.get("expiration")),
    )


def rdap_lookup(server, domain):
    """Registration data from an RDAP server, or None if the domain isn't registered there."""
    response = requests.get(
        f"{server}domain/{domain}",
        headers={"accept": "application/rdap+json"},
        timeout=TIMEOUT,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return parse_rdap(response.json(), domain)


# ---------- WHOIS ----------

def whois_query(server, query):
    """Raw WHOIS response: send the query to port 43 and read until the server closes."""
    chunks, size = [], 0
    with socket.create_connection((server, 43), timeout=TIMEOUT) as sock:
        sock.sendall(query.encode("ascii") + b"\r\n")
        while size < MAX_WHOIS_RESPONSE:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)
            size += len(data)
    return b"".join(chunks).decode("utf-8", errors="replace")


@functools.lru_cache(maxsize=256)
def whois_server(tld):
    """WHOIS server of a TLD as published by IANA (None if there is none)."""
    match = re.search(r"^whois:\s*(\S+)", whois_query(IANA_WHOIS_SERVER, tld), re.MULTILINE | re.IGNORECASE)
    return match.group(1) if match else None


def parse_whois(text, domain):
    """Pick registrar and dates out of a WHOIS response; None if there are none."""
    values = {}
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if not sep or not value:
            continue
        for field, names in WHOIS_FIELDS.items():
            if key in names and field not in values:
                values[field] = value

    if not values:
        return None  # "No entries found" and the like
    return DomainInfo(
        domain=domain,
        registrar=values.get("registrar"),
        created=parse_date(values.get("created")),
        expires=parse_date(values.get("expires")),
    )


_server_down_until = {}  # WHOIS server -> monotonic time to try it again


def whois_lookup(domain, tld):
    """Ask the registry's WHOIS server, falling back to mirrors if it is unreachable."""
    servers = [s for s in (whois_server(tld), *WHOIS_FALLBACK_SERVERS.get(tld, ())) if s]
    error = None
    for server in servers:
        if _server_down_until.get(server, 0) > time.monotonic():
            continue
        try:
            return parse_whois(whois_query(server, domain), domain)
        except OSError as e:
            log.warning("WHOIS server %s is unreachable: %s", server, e)
            _server_down_until[server] = time.monotonic() + SERVER_RETRY_AFTER
            error = e
    if error:
        raise error
    return None


# ---------- lookup ----------

_cache = {}  # domain -> (timestamp, DomainInfo | None)


def lookup_domain(domain):
    """Registration data of a domain (or of its parent for subdomains), None if unknown.

    Never raises: network problems just mean there is nothing to show.
    """
    now = time.monotonic()
    cached = _cache.get(domain)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]

    labels = domain.lower().split(".")
    tld = labels[-1]
    # mail.example.co.uk -> mail.example.co.uk, example.co.uk, co.uk
    candidates = [".".join(labels[i:]) for i in range(max(0, len(labels) - MAX_LEVELS), len(labels) - 1)]

    result = None
    try:
        server = rdap_servers().get(tld)
        for candidate in candidates:
            result = rdap_lookup(server, candidate) if server else whois_lookup(candidate, tld)
            if result:
                break
    except (requests.RequestException, OSError, ValueError) as e:
        log.warning("Domain lookup for %s failed: %s", domain, e)
        return None  # don't cache network errors

    if len(_cache) >= CACHE_MAX_SIZE:
        _cache.clear()
    _cache[domain] = (now, result)
    return result
