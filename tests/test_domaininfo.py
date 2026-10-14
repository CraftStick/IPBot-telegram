from datetime import datetime, timezone

import pytest
import requests

import domaininfo
from domaininfo import DomainInfo

RU_WHOIS = """\
domain:       YANDEX.RU
nserver:      ns1.yandex.ru. 213.180.193.1, 2a02:6b8::1
state:        REGISTERED, DELEGATED, VERIFIED
org:          YANDEX, LLC.
registrar:    RU-CENTER-RU
admin-contact:https://www.nic.ru/whois
created:      1997-09-23T09:45:07Z
paid-till:    2027-09-30T21:00:00Z
free-date:    2027-11-01
source:       TCI

Last updated on 2026-10-14T12:20:31Z
"""

GTLD_WHOIS = """\
   Domain Name: GITHUB.IO
   Registrar WHOIS Server: whois.markmonitor.com
   Registrar URL: http://www.markmonitor.com
   Updated Date: 2024-02-06T09:30:50Z
   Creation Date: 2013-03-08T19:12:48Z
   Registry Expiry Date: 2027-03-08T19:12:48Z
   Registrar: MarkMonitor Inc.
"""

RDAP_JSON = {
    "ldhName": "GOOGLE.COM",
    "events": [
        {"eventAction": "registration", "eventDate": "1997-09-15T04:00:00Z"},
        {"eventAction": "expiration", "eventDate": "2028-09-14T04:00:00Z"},
        {"eventAction": "last changed", "eventDate": "2019-09-09T15:39:04Z"},
    ],
    "entities": [
        {"roles": ["abuse"], "vcardArray": ["vcard", [["fn", {}, "text", "Abuse desk"]]]},
        {"roles": ["registrar"], "vcardArray": ["vcard", [["version", {}, "text", "4.0"], ["fn", {}, "text", "MarkMonitor Inc."]]]},
    ],
}


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def clean_state():
    domaininfo._cache.clear()
    domaininfo._server_down_until.clear()
    domaininfo._rdap_servers = None
    domaininfo.whois_server.cache_clear()


@pytest.mark.parametrize("value, expected", [
    ("1997-09-23T09:45:07Z", utc(1997, 9, 23, 9, 45, 7)),
    ("2031-12-15T14:48:05.81Z", utc(2031, 12, 15)),  # odd fraction: date part is used
    ("2027.10.01", utc(2027, 10, 1)),
    ("15-Sep-1997", utc(1997, 9, 15)),
    ("2027-03-01 (YYYY-MM-DD)", utc(2027, 3, 1)),
    ("before Aug-1996", None),
    ("", None),
    (None, None),
])
def test_parse_date(value, expected):
    parsed = domaininfo.parse_date(value)
    if expected is None:
        assert parsed is None
    else:
        assert parsed.date() == expected.date() and parsed.tzinfo is not None


def test_parse_whois_ru():
    assert domaininfo.parse_whois(RU_WHOIS, "yandex.ru") == DomainInfo(
        "yandex.ru", "RU-CENTER-RU", utc(1997, 9, 23, 9, 45, 7), utc(2027, 9, 30, 21, 0))


def test_parse_whois_gtld():
    info = domaininfo.parse_whois(GTLD_WHOIS, "github.io")
    assert info.registrar == "MarkMonitor Inc."  # not "Registrar WHOIS Server" / "Registrar URL"
    assert info.created.date() == utc(2013, 3, 8).date()
    assert info.expires.date() == utc(2027, 3, 8).date()


def test_parse_whois_not_found():
    assert domaininfo.parse_whois("No entries found for the selected source(s).\n", "nope.ru") is None


def test_parse_rdap():
    assert domaininfo.parse_rdap(RDAP_JSON, "google.com") == DomainInfo(
        "google.com", "MarkMonitor Inc.", utc(1997, 9, 15, 4), utc(2028, 9, 14, 4))


class FakeResponse:
    def __init__(self, data=None, status_code=200):
        self.data, self.status_code = data, status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return self.data


def test_lookup_uses_rdap_and_strips_subdomains(monkeypatch):
    requested = []

    def fake_get(url, headers=None, timeout=None):
        requested.append(url)
        if url == domaininfo.RDAP_BOOTSTRAP_URL:
            return FakeResponse({"services": [[["com", "net"], ["http://x/", "https://rdap.example/"]]]})
        if url.endswith("/domain/google.com"):
            return FakeResponse(RDAP_JSON)
        return FakeResponse(status_code=404)

    monkeypatch.setattr(domaininfo.requests, "get", fake_get)
    info = domaininfo.lookup_domain("a.mail.google.com")
    assert info.domain == "google.com"
    assert requested[1:] == [
        "https://rdap.example/domain/a.mail.google.com",
        "https://rdap.example/domain/mail.google.com",
        "https://rdap.example/domain/google.com",
    ]
    assert domaininfo.lookup_domain("a.mail.google.com") is info  # cached
    assert len(requested) == 4


def test_lookup_falls_back_to_whois_and_backup_server(monkeypatch):
    monkeypatch.setattr(domaininfo, "rdap_servers", lambda: {})  # .ru has no RDAP
    queries = []

    def fake_whois(server, query):
        queries.append((server, query))
        if server == domaininfo.IANA_WHOIS_SERVER:
            return "domain: RU\nwhois:        whois.tcinet.ru\n"
        if server == "whois.tcinet.ru":
            raise TimeoutError("timed out")
        return RU_WHOIS if query == "yandex.ru" else "No entries found\n"

    monkeypatch.setattr(domaininfo, "whois_query", fake_whois)
    assert domaininfo.lookup_domain("mail.yandex.ru").registrar == "RU-CENTER-RU"
    assert queries == [
        ("whois.iana.org", "ru"),
        ("whois.tcinet.ru", "mail.yandex.ru"),
        ("whois.nic.ru", "mail.yandex.ru"),
        ("whois.nic.ru", "yandex.ru"),  # the dead server is skipped now
    ]


def test_lookup_network_error_is_not_cached(monkeypatch):
    monkeypatch.setattr(domaininfo, "rdap_servers", lambda: {"com": "https://rdap.example/"})

    def fail(*args, **kwargs):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(domaininfo.requests, "get", fail)
    assert domaininfo.lookup_domain("google.com") is None
    assert domaininfo._cache == {}


def test_lookup_unknown_tld(monkeypatch):
    monkeypatch.setattr(domaininfo, "rdap_servers", lambda: {})
    monkeypatch.setattr(domaininfo, "whois_query", lambda server, query: "domain: LOCAL\n")
    assert domaininfo.lookup_domain("example.local") is None
