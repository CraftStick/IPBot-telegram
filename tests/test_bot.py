from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
import requests
import telebot

import bot
from domaininfo import DomainInfo
from texts import NETWORK_EMOJI, PIN_EMOJI, TEXTS, format_duration, get_lang, t

GOOGLE_DNS = {
    "status": "success",
    "query": "8.8.8.8",
    "country": "United States",
    "countryCode": "US",
    "regionName": "Virginia",
    "city": "Ashburn",
    "timezone": "America/New_York",
    "isp": "Google LLC",
    "org": "Google Public DNS",
    "as": "AS15169 Google LLC",
    "asname": "GOOGLE",
    "reverse": "dns.google",
    "continent": "North America",
    "zip": "20149",
    "lat": 39.03,
    "lon": -77.5,
    "mobile": False,
}


class FakeResponse:
    def __init__(self, data=None, status_code=200):
        self.data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self.data


@pytest.fixture(autouse=True)
def clear_cache():
    bot._cache.clear()


@pytest.fixture(autouse=True)
def whois(monkeypatch):
    """WHOIS without network: set whois.result, inspect whois.calls."""
    state = SimpleNamespace(result=None, calls=[])

    def lookup_domain(domain):
        state.calls.append(domain)
        return state.result

    monkeypatch.setattr(bot.domaininfo, "lookup_domain", lookup_domain)
    return state


@pytest.fixture
def api(monkeypatch):
    """Replace ip-api with a fake; set api.response and inspect api.calls."""
    state = SimpleNamespace(response=FakeResponse(GOOGLE_DNS), calls=[])

    def fake_get(url, params=None, timeout=None):
        state.calls.append((url, params))
        if isinstance(state.response, Exception):
            raise state.response
        return state.response

    monkeypatch.setattr(bot.requests, "get", fake_get)
    return state


@pytest.fixture
def sent(monkeypatch):
    """Capture everything the bot sends instead of calling Telegram."""
    calls = []
    for method in ("reply_to", "send_message", "send_venue", "answer_inline_query"):
        monkeypatch.setattr(
            bot.bot, method,
            lambda *args, _m=method, **kwargs: calls.append((_m, args, kwargs)),
        )
    monkeypatch.setattr(bot, "bot_username", lambda: "test_bot")
    return calls


def make_message(text, lang="en", chat_type="private", via_bot=None):
    return SimpleNamespace(
        text=text,
        message_id=7,
        via_bot=via_bot,
        chat=SimpleNamespace(id=1, type=chat_type),
        from_user=SimpleNamespace(first_name="Ann", language_code=lang),
    )


# ---------- input parsing ----------

@pytest.mark.parametrize("text, expected", [
    ("8.8.8.8", "8.8.8.8"),
    ("  8.8.8.8:53 ", "8.8.8.8"),
    ("2606:4700::1111", "2606:4700::1111"),
    ("[2606:4700::1111]:443", "2606:4700::1111"),
    ("http://[2001:db8::1]:8080/path", "2001:db8::1"),
    ("https://google.com/search?q=1", "google.com"),
    ("Example.COM.", "example.com"),
    ("google.com:443", "google.com"),
    ("пример.рф", "xn--e1afmkfd.xn--p1ai"),
    ("1.2.3.999", None),
    ("hello", None),
    ("localhost", None),
    ("-bad-.com", None),
    ("http://[::1", None),
    ("", None),
])
def test_normalize_query(text, expected):
    assert bot.normalize_query(text) == expected


@pytest.mark.parametrize("code, flag", [("US", "🇺🇸"), ("ru", "🇷🇺"), ("", "🏳️"), (None, "🏳️"), ("USA", "🏳️")])
def test_get_emoji_flag(code, flag):
    assert bot.get_emoji_flag(code) == flag


# ---------- ip-api lookups ----------

def test_lookup_success_and_cache(api):
    assert bot.get_ip_info("8.8.8.8") == GOOGLE_DNS
    assert bot.get_ip_info("8.8.8.8") == GOOGLE_DNS
    assert len(api.calls) == 1
    assert "lang" not in api.calls[0][1]


def test_lookup_passes_language(api):
    bot.get_ip_info("8.8.8.8", "ru")
    bot.get_ip_info("8.8.8.8", "en")
    assert api.calls[0][1]["lang"] == "ru"
    assert len(api.calls) == 2  # cached separately per language


@pytest.mark.parametrize("ip, key", [("192.168.1.1", "err_private"), ("127.0.0.1", "err_private"), ("100.64.0.1", "err_reserved")])
def test_lookup_rejects_non_public_ip_without_request(api, ip, key):
    with pytest.raises(bot.LookupFailed) as e:
        bot.get_ip_info(ip)
    assert e.value.key == key
    assert api.calls == []


@pytest.mark.parametrize("response, key", [
    (FakeResponse({"status": "fail", "message": "invalid query"}), "err_invalid"),
    (FakeResponse({"status": "fail", "message": "something new"}), "err_unknown"),
    (FakeResponse(status_code=429), "err_rate_limit"),
    (FakeResponse(status_code=503), "err_unavailable"),
    (requests.ConnectionError("offline"), "err_unavailable"),
])
def test_lookup_errors(api, response, key):
    api.response = response
    with pytest.raises(bot.LookupFailed) as e:
        bot.get_ip_info("example.com")
    assert e.value.key == key


def test_errors_are_not_cached(api):
    api.response = FakeResponse(status_code=429)
    with pytest.raises(bot.LookupFailed):
        bot.get_ip_info("8.8.8.8")
    api.response = FakeResponse(GOOGLE_DNS)
    assert bot.get_ip_info("8.8.8.8") == GOOGLE_DNS


# ---------- formatting ----------

NOON_UTC = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)


def test_format_ip_info_en():
    text = bot.format_ip_info(GOOGLE_DNS, "8.8.8.8", now=NOON_UTC)
    assert text.startswith("🇺🇸 <code>8.8.8.8</code> · IPv4\n")
    assert f"{PIN_EMOJI} <b>Location</b>\n<blockquote>Ashburn, Virginia, United States\n" in text
    assert "<b>Continent:</b> North America\n" in text
    assert "<b>ZIP code:</b> <code>20149</code>\n" in text
    assert "<b>Timezone:</b> America/New_York (UTC−5), now 07:00\n" in text
    assert "Currency" not in text
    assert "<b>Coordinates:</b> <code>39.03, -77.5</code></blockquote>" in text
    assert "<b>Organization:</b> Google Public DNS" in text
    assert "<b>AS:</b> AS15169 (GOOGLE)\n" in text
    assert "<b>Hostname:</b> <code>dns.google</code></blockquote>" in text
    assert text.endswith("<b>Hostname:</b> <code>dns.google</code></blockquote>")  # no tags for non-mobile


def test_format_ip_info_marks_mobile_network():
    text = bot.format_ip_info({**GOOGLE_DNS, "mobile": True}, "8.8.8.8", "ru", now=NOON_UTC)
    assert text.endswith("\n\n<blockquote>📱 Мобильная сеть</blockquote>")


def test_format_ip_info_ru_with_domain():
    text = bot.format_ip_info(GOOGLE_DNS, "dns.google", "ru", now=NOON_UTC)
    assert text.startswith("🇺🇸 <b>dns.google</b>\n<code>8.8.8.8</code> · IPv4\n")
    assert f"{PIN_EMOJI} <b>Местоположение</b>" in text
    assert f"{NETWORK_EMOJI} <b>Сеть</b>" in text
    assert "сейчас 07:00" in text
    assert "<b>Провайдер:</b> Google LLC" in text


def test_format_ip_info_shows_idn_domain_in_unicode():
    text = bot.format_ip_info(GOOGLE_DNS, "xn--e1afmkfd.xn--p1ai", "ru", now=NOON_UTC)
    assert text.startswith("🇺🇸 <b>пример.рф</b>\n")


def test_format_skips_empty_and_repeated_values():
    info = {"query": "77.88.55.88", "city": "Москва", "regionName": "Москва", "country": "Россия",
            "isp": "Yandex LLC", "org": "YANDEX LLC", "as": "AS13238 YANDEX LLC"}
    text = bot.format_ip_info(info, "77.88.55.88", "ru")
    assert "<blockquote>Москва, Россия</blockquote>" in text
    assert "Организация" not in text  # same as ISP ignoring case
    assert "<b>AS:</b> AS13238</blockquote>" in text
    assert "Часовой пояс" not in text and "Координаты" not in text and "Хост" not in text


def test_format_shows_as_name_when_new():
    info = {"query": "1.1.1.1", "isp": "Cloudflare, Inc", "as": "AS13335 Cloudflare Net"}
    assert "AS13335 Cloudflare Net" in bot.format_ip_info(info, "1.1.1.1")


@pytest.mark.parametrize("tz, expected", [
    ("Asia/Kolkata", "Asia/Kolkata (UTC+5:30), now 17:30"),
    ("Europe/Moscow", "Europe/Moscow (UTC+3), now 15:00"),
    ("Etc/UTC", "Etc/UTC (UTC+0), now 12:00"),
    ("Mars/Olympus", "Mars/Olympus"),
])
def test_format_timezone(tz, expected):
    assert bot.format_timezone(tz, "en", NOON_UTC) == expected


def test_format_escapes_html_and_keeps_zero_coordinates():
    info = {"query": "1.1.1.1", "isp": "<b>Evil</b> & Co", "lat": 0, "lon": 0}
    text = bot.format_ip_info(info, "1.1.1.1")
    assert "&lt;b&gt;Evil&lt;/b&gt; &amp; Co" in text
    assert "<code>0, 0</code>" in text


def test_venue_texts():
    assert bot.venue_texts(GOOGLE_DNS) == ("Ashburn, Virginia, United States", "8.8.8.8 · Google LLC")
    assert bot.venue_texts({"query": "1.1.1.1"}) == ("1.1.1.1", "1.1.1.1")


# ---------- WHOIS ----------

GOOGLE_WHOIS = DomainInfo(
    "google.com", "MarkMonitor Inc.",
    datetime(1997, 9, 15, 4, tzinfo=timezone.utc), datetime(2028, 9, 14, 4, tzinfo=timezone.utc),
)


def test_format_whois_section():
    text = bot.format_ip_info(GOOGLE_DNS, "google.com", "ru", now=NOON_UTC, whois=GOOGLE_WHOIS)
    assert ("🌐 <b>WHOIS</b>\n<blockquote><b>Регистратор:</b> MarkMonitor Inc.\n"
            "<b>Зарегистрирован:</b> 15.09.1997 (28 лет назад)\n"
            "<b>Истекает:</b> 14.09.2028 (через 2 года)</blockquote>") in text
    assert "<b>Домен:</b>" not in text


def test_format_whois_for_subdomain_and_expiry():
    soon = DomainInfo("google.com", None, None, datetime(2026, 1, 20, tzinfo=timezone.utc))
    text = bot.format_ip_info(GOOGLE_DNS, "mail.google.com", "en", now=NOON_UTC, whois=soon)
    assert "<b>Domain:</b> <code>google.com</code>\n⚠️ <b>Expires:</b> 2026-01-20 (in 5 days)" in text

    expired = DomainInfo("google.com", None, None, datetime(2025, 1, 20, tzinfo=timezone.utc))
    text = bot.format_ip_info(GOOGLE_DNS, "google.com", "ru", now=NOON_UTC, whois=expired)
    assert "⚠️ <b>Истёк:</b> 20.01.2025</blockquote>" in text


def test_whois_only_for_domains(api, whois):
    whois.result = GOOGLE_WHOIS
    assert bot.lookup("8.8.8.8") == (GOOGLE_DNS, None)
    assert bot.lookup("google.com") == (GOOGLE_DNS, GOOGLE_WHOIS)
    assert whois.calls == ["google.com"]


def test_card_includes_whois(api, sent, whois):
    whois.result = GOOGLE_WHOIS
    bot.ip_command(make_message("/ip google.com"))
    assert "MarkMonitor Inc." in sent[-1][1][1]


@pytest.mark.parametrize("days, ru, en", [
    (1, "1 день", "1 day"), (3, "3 дня", "3 days"), (11, "11 дней", "11 days"), (21, "21 день", "21 days"),
    (45, "1 месяц", "1 month"), (100, "3 месяца", "3 months"), (365 * 5, "5 лет", "5 years"),
    (365 * 22, "22 года", "22 years"), (365 * 111, "111 лет", "111 years"), (-400, "1 год", "1 year"),
])
def test_format_duration(days, ru, en):
    assert format_duration("ru", days) == ru
    assert format_duration("en", days) == en


# ---------- languages ----------

@pytest.mark.parametrize("code, lang", [("ru", "ru"), ("ru-RU", "ru"), ("en", "en"), ("de", "en"), (None, "en")])
def test_get_lang(code, lang):
    assert get_lang(SimpleNamespace(language_code=code)) == lang


def test_translations_have_same_keys():
    assert set(TEXTS["ru"]) == set(TEXTS["en"])


def test_all_texts_format():
    for lang in TEXTS:
        for key in TEXTS[lang]:
            t(lang, key, name="Ann", bot="test_bot", message="x", place="Paris", time="12:00", duration="1 day")


# ---------- handlers ----------

def test_map_pin_then_card(api, sent):
    bot.handle_text(make_message("8.8.8.8"))
    assert [c[0] for c in sent] == ["send_venue", "send_message"]
    _, venue_args, venue_kwargs = sent[0]
    assert venue_args == (1, 39.03, -77.5, "Ashburn, Virginia, United States", "8.8.8.8 · Google LLC")
    assert venue_kwargs["reply_to_message_id"] == 7  # only the map quotes the request
    _, args, kwargs = sent[1]
    assert args[0] == 1 and "Ashburn" in args[1]
    assert "reply_markup" not in kwargs  # no buttons under the card


def test_map_failure_still_sends_card(api, sent, monkeypatch):
    def fail(*args, **kwargs):
        raise telebot.apihelper.ApiTelegramException("sendVenue", "", {"error_code": 400, "description": "Bad Request"})

    monkeypatch.setattr(bot.bot, "send_venue", fail)
    bot.handle_text(make_message("8.8.8.8"))
    assert [c[0] for c in sent] == ["reply_to"]
    assert "Ashburn" in sent[0][1][1]


def test_no_map_without_coordinates(api, sent):
    api.response = FakeResponse({k: v for k, v in GOOGLE_DNS.items() if k not in ("lat", "lon")})
    bot.handle_text(make_message("8.8.8.8"))
    assert [c[0] for c in sent] == ["reply_to"]


def test_invalid_input_in_russian(api, sent):
    bot.handle_text(make_message("привет", lang="ru"))
    assert sent[0][1][1].startswith("❌ Это не похоже на IP-адрес")
    assert api.calls == []


def test_lookup_error_reply(api, sent):
    bot.handle_text(make_message("10.0.0.1"))
    assert sent[0][1][1] == "❌ " + t("en", "err_private")


def test_group_messages_and_inline_echo_are_ignored(api, sent):
    bot.handle_text(make_message("8.8.8.8", chat_type="group"))
    bot.handle_text(make_message("8.8.8.8", via_bot=SimpleNamespace(id=42)))
    assert sent == []


def test_ip_command(api, sent):
    bot.ip_command(make_message("/ip"))
    assert "/ip 8.8.8.8" in sent[0][1][1]
    bot.ip_command(make_message("/ip@test_bot google.com"))
    assert api.calls[0][0].endswith("/google.com")


def test_start_escapes_name(sent):
    message = make_message("/start")
    message.from_user.first_name = "<script>"
    bot.start_command(message)
    assert "&lt;script&gt;" in sent[0][1][1]
    assert "@test_bot" in sent[0][1][1]


def test_inline_query_results(api, sent):
    bot.handle_inline_query(SimpleNamespace(id="q1", query="8.8.8.8", from_user=SimpleNamespace(language_code="ru")))
    method, args, kwargs = sent[0]
    results = args[1]
    assert method == "answer_inline_query"
    assert [r.type for r in results] == ["article", "venue"]
    assert results[1].title == "Ashburn, Virginia, United States"
    assert results[1].thumbnail_url == bot.PIN_THUMBNAIL_URL
    assert results[0].title == "🇺🇸 8.8.8.8"
    message_text = results[0].input_message_content.message_text
    assert "📍 <b>Местоположение</b>" in message_text
    assert "📡 <b>Сеть</b>" in message_text
    assert "<tg-emoji" not in message_text  # animated emoji only work in the bot's own messages
    assert results[0].reply_markup is None
    assert kwargs["button"] is None
    assert kwargs["is_personal"] is True  # results are localized per user


def test_start_help_from_inline_button_shows_help(sent):
    bot.start_command(make_message("/start help"))
    assert sent[0][1][1] == t("en", "help", bot="test_bot")


def test_inline_query_invalid_shows_hint(api, sent):
    bot.handle_inline_query(SimpleNamespace(id="q2", query="goo", from_user=SimpleNamespace(language_code="en")))
    _, args, kwargs = sent[0]
    assert args[1] == []
    assert kwargs["button"].text == t("en", "inline_hint")
    assert api.calls == []
