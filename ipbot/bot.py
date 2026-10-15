"""IP Info Telegram Bot: geolocation lookup for any IP address or domain."""

import functools
import html
import ipaddress
import logging
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests
import telebot
from telebot import types

import domaininfo
from texts import DEFAULT_LANG, LANGUAGES, NETWORK_EMOJI, PIN_EMOJI, format_duration, get_lang, t

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("ipbot")

# ip-api.com free tier: HTTP only, 45 requests per minute for the whole bot
API_URL = "http://ip-api.com/json/{}"
API_FIELDS = (
    "status,message,query,continent,country,countryCode,regionName,city,district,zip,"
    "timezone,isp,org,as,asname,reverse,lat,lon,mobile"
)
API_TIMEOUT = 5
CACHE_TTL = 300  # seconds
CACHE_MAX_SIZE = 1000
INLINE_CACHE_TIME = 300  # seconds Telegram caches inline results
# Pixel-art pin picture for the map result in inline mode: docs/pin.jpg from the repo via the jsDelivr CDN
PIN_THUMBNAIL_URL = "https://cdn.jsdelivr.net/gh/CraftStick/IPBot-telegram@main/docs/pin.jpg"
PIN_THUMBNAIL_SIZE = 136
WHOIS_WAIT = 6  # seconds to wait for WHOIS after the geolocation is ready
EXPIRY_WARNING_DAYS = 30

API_ERRORS = {
    "private range": "err_private",
    "reserved range": "err_reserved",
    "invalid query": "err_invalid",
}

PLACEHOLDER_TOKENS = {"", "YOUR_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE"}

DOMAIN_RE = re.compile(
    r"(?=.{1,253}$)((?!-)[a-z0-9-]{1,63}(?<!-)\.)+(?!-)[a-z0-9-]{2,63}(?<!-)"
)


class LookupFailed(Exception):
    """Lookup error that can be shown to the user in their language."""

    def __init__(self, key, **params):
        super().__init__(key)
        self.key = key
        self.params = params

    def text(self, lang):
        return t(lang, self.key, **{k: html.escape(str(v)) for k, v in self.params.items()})


def load_token():
    """Read the bot token from the BOT_TOKEN env variable or config.py."""
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        try:
            from config import BOT_TOKEN
            token = (BOT_TOKEN or "").strip()
        except ImportError:
            pass

    if token in PLACEHOLDER_TOKENS:
        sys.exit(
            "❌ Bot token is not set.\n"
            "Set the BOT_TOKEN environment variable or copy config.example.py "
            "to config.py and put your token from @BotFather there."
        )
    return token


# A lookup can block a worker for API_TIMEOUT + WHOIS_WAIT seconds, so keep more than the default 2
bot = telebot.TeleBot(load_token(), parse_mode="HTML", num_threads=8)


@functools.lru_cache(maxsize=None)
def bot_username():
    return bot.get_me().username


def get_emoji_flag(country_code):
    """Convert country code to emoji flag."""
    if not country_code or len(country_code) != 2:
        return "🏳️"

    # 'A' -> U+1F1E6, 'B' -> U+1F1E7, etc.
    return "".join(chr(ord(ch) + 127397) for ch in country_code.upper())


def normalize_query(text):
    """Turn user input into an IP address or ASCII domain name, or None if it is invalid.

    Accepts plain IPs/domains as well as URLs and host:port pairs.
    """
    query = text.strip()
    if "://" in query:
        try:
            query = urlsplit(query).hostname or ""
        except ValueError:  # malformed URL, e.g. "http://[::1"
            return None
    else:
        query = query.split("/")[0]
    query = query.strip()
    if query.startswith("[") and "]" in query:  # [IPv6]:port
        query = query[1:query.index("]")]
    query = query.rstrip(".").lower()

    candidates = [query]
    if query.count(":") == 1:  # host:port (IPv6 addresses contain several colons)
        candidates.append(query.split(":")[0])

    for candidate in candidates:
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            pass

    host = candidates[-1]
    try:
        host = host.encode("idna").decode("ascii")  # пример.рф -> xn--e1afmkfd.xn--p1ai
    except UnicodeError:
        return None

    if DOMAIN_RE.fullmatch(host) and not re.fullmatch(r"[\d.]+", host):
        return host
    return None


def is_ip(query):
    try:
        ipaddress.ip_address(query)
        return True
    except ValueError:
        return False


def display_domain(domain):
    """Punycode back to Unicode for showing: xn--e1afmkfd.xn--p1ai -> пример.рф."""
    try:
        return domain.encode("ascii").decode("idna")
    except UnicodeError:
        return domain


_cache = {}  # (query, lang) -> (timestamp, data)
_cache_lock = threading.Lock()  # handlers run in several worker threads


def get_ip_info(query, lang=DEFAULT_LANG):
    """Get geolocation data for a normalized IP address or domain (cached)."""
    try:
        ip = ipaddress.ip_address(query)
    except ValueError:
        ip = None  # a domain
    if ip is not None and not ip.is_global:
        raise LookupFailed("err_private" if ip.is_private else "err_reserved")

    now = time.monotonic()
    cache_key = (query, lang)
    with _cache_lock:
        cached = _cache.get(cache_key)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]

    params = {"fields": API_FIELDS}
    if lang != DEFAULT_LANG:
        params["lang"] = lang  # localized country/region/city names
    try:
        response = requests.get(API_URL.format(query), params=params, timeout=API_TIMEOUT)
        if response.status_code == 429:
            raise LookupFailed("err_rate_limit")
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        log.warning("ip-api request for %s failed: %s", query, e)
        raise LookupFailed("err_unavailable")

    if data.get("status") != "success":
        message = data.get("message", "unknown error")
        if message in API_ERRORS:
            raise LookupFailed(API_ERRORS[message])
        raise LookupFailed("err_unknown", message=message)

    with _cache_lock:
        if len(_cache) >= CACHE_MAX_SIZE:
            for key in [k for k, (ts, _) in _cache.items() if now - ts >= CACHE_TTL]:
                del _cache[key]
            if len(_cache) >= CACHE_MAX_SIZE:
                _cache.clear()
        _cache[cache_key] = (now, data)
    return data


_whois_pool = ThreadPoolExecutor(max_workers=4)


def lookup(query, lang=DEFAULT_LANG):
    """Geolocation and, for domains, WHOIS data (fetched in parallel). Raises LookupFailed."""
    whois_future = None if is_ip(query) else _whois_pool.submit(domaininfo.lookup_domain, query)
    info = get_ip_info(query, lang)

    whois = None
    if whois_future:
        try:
            whois = whois_future.result(timeout=WHOIS_WAIT)
        except Exception as e:
            log.warning("WHOIS for %s took too long or failed: %s", query, e)
    return info, whois


def has_coordinates(info):
    return info.get("lat") is not None and info.get("lon") is not None


def format_place(info, with_region=False):
    """"City, Region, Country" without empty parts and repeats (Moscow, Moscow)."""
    fields = ("district", "city", "regionName", "country") if with_region else ("city", "country")
    parts = []
    for value in (info.get(f) for f in fields):
        if value and value not in parts:
            parts.append(value)
    return ", ".join(parts)


def format_utc_offset(offset):
    minutes = int(offset.total_seconds() // 60)
    hours, mins = divmod(abs(minutes), 60)
    return f"UTC{'+' if minutes >= 0 else '−'}{hours}" + (f":{mins:02d}" if mins else "")


def format_timezone(tz_name, lang, now=None):
    """"Europe/Moscow (UTC+3), now 14:05" or just the name if it is unknown."""
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError):
        return html.escape(tz_name)

    local = (now or datetime.now(timezone.utc)).astimezone(tz)
    return (
        f"{html.escape(tz_name)} ({format_utc_offset(local.utcoffset())}), "
        f"{t(lang, 'local_time', time=local.strftime('%H:%M'))}"
    )


def format_as(info):
    """"AS15169 Google LLC" -> "AS15169 (GOOGLE)" using the short AS name when there is one.

    Without it the full name is kept only if ISP/org don't show it already.
    """
    number, _, name = info["as"].partition(" ")
    if info.get("asname"):
        return f"{number} ({info['asname']})"
    known = {(info.get(k) or "").lower() for k in ("isp", "org")}
    return info["as"] if name and name.lower() not in known else number


def format_date(value, lang, now):
    """"15.09.1997 (29 лет назад)" / "14.09.2028 (через 1 год)"."""
    days = (value.date() - now.date()).days
    if days == 0:
        relative = t(lang, "today")
    else:
        relative = t(lang, "in" if days > 0 else "ago", duration=format_duration(lang, days))
    return f"{value.strftime(t(lang, 'date_format'))} ({relative})"


def row(lang, key, value):
    """One "<b>Label:</b> value" line of a card section."""
    return f"<b>{t(lang, key)}:</b> {value}"


def format_whois(whois, query, lang, now):
    """Rows of the WHOIS section."""
    rows = []
    if whois.domain != query:  # data of the parent domain for a subdomain
        rows.append(row(lang, "domain", f"<code>{html.escape(display_domain(whois.domain))}</code>"))
    if whois.registrar:
        rows.append(row(lang, "registrar", html.escape(whois.registrar)))
    if whois.created:
        rows.append(row(lang, "registered", format_date(whois.created, lang, now)))
    if whois.expires:
        days_left = (whois.expires.date() - now.date()).days
        if days_left < 0:
            rows.append("⚠️ " + row(lang, "expired", whois.expires.strftime(t(lang, "date_format"))))
        else:
            warning = "⚠️ " if days_left <= EXPIRY_WARNING_DAYS else ""
            rows.append(warning + row(lang, "expires", format_date(whois.expires, lang, now)))
    return rows


def format_ip_info(info, query, lang=DEFAULT_LANG, now=None, whois=None, animated=True):
    """Format IP information into an HTML message.

    animated=False keeps plain emoji: Telegram allows animated (custom) emoji only
    in messages the bot sends itself, not in ones sent via inline mode.
    """
    esc = html.escape
    ip = info.get("query", query)
    flag = get_emoji_flag(info.get("countryCode"))
    try:
        version = f" · IPv{ipaddress.ip_address(ip).version}"
    except ValueError:
        version = ""

    if query != ip:
        lines = [f"{flag} <b>{esc(display_domain(query))}</b>", f"<code>{esc(ip)}</code>{version}"]
    else:
        lines = [f"{flag} <code>{esc(ip)}</code>{version}"]

    def section(emoji, key, rows):
        if rows:
            lines.extend(["", f"{emoji} <b>{t(lang, key)}</b>", "<blockquote>" + "\n".join(rows) + "</blockquote>"])

    location = []
    place = format_place(info, with_region=True)
    if place:
        location.append(esc(place))
    if info.get("continent"):
        location.append(row(lang, "continent", esc(info["continent"])))
    if info.get("zip"):
        location.append(row(lang, "zip", f"<code>{esc(info['zip'])}</code>"))
    if info.get("timezone"):
        location.append(row(lang, "timezone", format_timezone(info["timezone"], lang, now)))
    if has_coordinates(info):
        location.append(row(lang, "coords", f"<code>{info['lat']}, {info['lon']}</code>"))
    section(PIN_EMOJI if animated else "📍", "section_location", location)

    network = []
    if info.get("isp"):
        network.append(row(lang, "isp", esc(info["isp"])))
    if info.get("org") and info["org"].lower() != (info.get("isp") or "").lower():
        network.append(row(lang, "org", esc(info["org"])))
    if info.get("as"):
        network.append(row(lang, "as", esc(format_as(info))))
    if info.get("reverse"):
        network.append(row(lang, "reverse", f"<code>{esc(info['reverse'])}</code>"))
    section(NETWORK_EMOJI if animated else "📡", "section_network", network)

    if whois:
        section("🌐", "section_whois", format_whois(whois, query, lang, now or datetime.now(timezone.utc)))

    if info.get("mobile"):
        lines += ["", f"<blockquote>{t(lang, 'tag_mobile')}</blockquote>"]

    return "\n".join(lines)


def venue_texts(info):
    """Title and address for the map pin: "City, Region, Country" and "IP · ISP"."""
    ip = info["query"]
    title = format_place(info, with_region=True) or ip
    address = " · ".join(v for v in (ip, info.get("isp")) if v)
    return title, address


def reply_with_lookup(message, text):
    """Look up the IP/domain from the user's text and reply with the result."""
    lang = get_lang(message.from_user)
    query = normalize_query(text)
    if not query:
        bot.reply_to(message, t(lang, "invalid_input"))
        return

    try:
        info, whois = lookup(query, lang)
    except LookupFailed as e:
        bot.reply_to(message, f"❌ {e.text(lang)}")
        return

    card = format_ip_info(info, query, lang, whois=whois)

    # Telegram can't attach text to a map pin, so the interactive map goes first
    # and the card right below it (without quoting the request a second time)
    if has_coordinates(info):
        title, address = venue_texts(info)
        try:
            bot.send_venue(
                message.chat.id, info["lat"], info["lon"], title, address,
                reply_to_message_id=message.message_id,
            )
        except telebot.apihelper.ApiException as e:
            log.warning("Could not send the map for %s: %s", query, e)
        else:
            bot.send_message(message.chat.id, card, disable_web_page_preview=True)
            return

    bot.reply_to(message, card, disable_web_page_preview=True)


# ========================================
# COMMANDS
# ========================================
@bot.message_handler(commands=["start"])
def start_command(message):
    # "/start help" comes from the hint button in inline mode
    if telebot.util.extract_arguments(message.text or "") == "help":
        help_command(message)
        return
    lang = get_lang(message.from_user)
    name = html.escape(message.from_user.first_name or "")
    bot.send_message(
        message.chat.id,
        t(lang, "start", name=name, bot=bot_username()),
        reply_markup=types.ReplyKeyboardRemove(),  # remove the keyboard from older bot versions
        disable_web_page_preview=True,
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(message.chat.id, t(get_lang(message.from_user), "help", bot=bot_username()))


@bot.message_handler(commands=["ip", "info"])
def ip_command(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, t(get_lang(message.from_user), "need_address"))
        return
    reply_with_lookup(message, parts[1])


@bot.message_handler(content_types=["text"])
def handle_text(message):
    # In groups only commands are handled; messages sent via inline mode are ours already
    if message.chat.type != "private" or message.via_bot:
        return
    if message.text.startswith("/"):
        bot.reply_to(message, t(get_lang(message.from_user), "unknown_command"))
        return
    reply_with_lookup(message, message.text)


# ========================================
# INLINE MODE (@bot 8.8.8.8 in any chat)
# ========================================
@bot.inline_handler(func=lambda inline_query: True)
def handle_inline_query(inline_query):
    lang = get_lang(inline_query.from_user)
    query = normalize_query(inline_query.query)
    results = []

    if query:
        try:
            info, whois = lookup(query, lang)
        except LookupFailed:
            info, whois = None, None

        if info:
            ip = info.get("query", query)
            place = format_place(info)
            description = " · ".join(v for v in (place, info.get("isp")) if v)
            results.append(types.InlineQueryResultArticle(
                id="info",
                title=f"{get_emoji_flag(info.get('countryCode'))} {ip}",
                description=description,
                input_message_content=types.InputTextMessageContent(
                    format_ip_info(info, query, lang, whois=whois, animated=False),
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                ),
            ))
            if has_coordinates(info):
                title, address = venue_texts(info)
                results.append(types.InlineQueryResultVenue(
                    id="location",
                    title=title,
                    latitude=info["lat"],
                    longitude=info["lon"],
                    address=address,
                    thumbnail_url=PIN_THUMBNAIL_URL,
                    thumbnail_width=PIN_THUMBNAIL_SIZE,
                    thumbnail_height=PIN_THUMBNAIL_SIZE,
                ))

    button = None
    if not results:
        button = types.InlineQueryResultsButton(t(lang, "inline_hint"), start_parameter="help")
    # Results depend on the user's language, so Telegram must not share them between users
    bot.answer_inline_query(
        inline_query.id, results, cache_time=INLINE_CACHE_TIME, is_personal=True, button=button,
    )


# ========================================
# BOT STARTUP
# ========================================
def setup_commands():
    """Register the command menu in every supported language."""
    for lang in LANGUAGES:
        commands = [
            types.BotCommand("ip", t(lang, "cmd_ip")),
            types.BotCommand("help", t(lang, "cmd_help")),
            types.BotCommand("start", t(lang, "cmd_start")),
        ]
        try:
            bot.set_my_commands(commands, language_code=None if lang == DEFAULT_LANG else lang)
        except Exception as e:
            log.warning("Could not set %s commands: %s", lang, e)


if __name__ == "__main__":
    setup_commands()
    log.info("Bot @%s started, waiting for messages...", bot_username())
    # infinity_polling reconnects on network errors by itself
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
