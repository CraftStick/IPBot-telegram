"""User-facing texts in English and Russian."""

DEFAULT_LANG = "en"

EXAMPLES = "<code>8.8.8.8</code>, <code>2606:4700::1111</code>, <code>google.com</code>"

# Animated (custom) emoji. They need the bot owner to have Telegram Premium;
# otherwise Telegram shows the plain emoji inside the tag.
WAVE_EMOJI = '<tg-emoji emoji-id="5222459157084411333">👋</tg-emoji>'
CHAT_EMOJI = '<tg-emoji emoji-id="5294450432532323035">💬</tg-emoji>'
PIN_EMOJI = '<tg-emoji emoji-id="5226924660351840411">📍</tg-emoji>'
NETWORK_EMOJI = '<tg-emoji emoji-id="5426842241085743267">🤪</tg-emoji>'  # replaces 📡 in the Network header

TEXTS = {
    "en": {
        "start": (
            WAVE_EMOJI + " Hello, {name}!\n\n"
            "Send me an <b>IP address</b> or a <b>domain</b> and I'll show its location, "
            "provider and more.\n\nExamples: {examples}\n\n"
            + CHAT_EMOJI + " Works in any chat too: type <code>@{bot} 8.8.8.8</code>"
        ),
        "help": (
            "📚 <b>How to use</b>\n\n"
            "Just send an IP address, domain or link, or use a command:\n\n"
            "/ip <code>&lt;address&gt;</code> - look up an IP or domain\n"
            "/info <code>&lt;address&gt;</code> - same as /ip\n"
            "/start - welcome message\n"
            "/help - this message\n\n"
            "💬 <b>Inline mode:</b> in any chat type <code>@{bot} google.com</code> "
            "and pick the result.\n\n"
            "⚙️ <b>Bot shows:</b>\n"
            "• Location on the map\n"
            "• Country with flag, region, city and ZIP code\n"
            "• Timezone with local time\n"
            "• Internet provider, organization and AS\n"
            "• Hostname (PTR)\n"
            "• Domain registrar and registration dates (WHOIS)\n"
            "• Mobile network flag"
        ),
        "need_address": "Send an address after the command, e.g. <code>/ip 8.8.8.8</code>\nExamples: {examples}",
        "unknown_command": "🤖 Unknown command. See /help",
        "invalid_input": "❌ That doesn't look like an IP address or domain.\nExamples: {examples}",
        "section_location": "Location",
        "section_network": "Network",
        "local_time": "now {time}",
        "continent": "Continent",
        "zip": "ZIP code",
        "timezone": "Timezone",
        "coords": "Coordinates",
        "isp": "ISP",
        "org": "Organization",
        "as": "AS",
        "reverse": "Hostname",
        "section_whois": "WHOIS",
        "domain": "Domain",
        "registrar": "Registrar",
        "registered": "Registered",
        "expires": "Expires",
        "expired": "Expired",
        "ago": "{duration} ago",
        "in": "in {duration}",
        "today": "today",
        "date_format": "%Y-%m-%d",
        "tag_mobile": "📱 Mobile network",
        "err_private": "This is a private network address, it has no public location.",
        "err_reserved": "This is a reserved address, it has no public location.",
        "err_invalid": "Could not resolve this IP address or domain.",
        "err_rate_limit": "Too many requests right now. Please try again in a minute.",
        "err_unavailable": "Geolocation service is unavailable. Please try again later.",
        "err_unknown": "Lookup failed: {message}",
        "inline_hint": "ℹ️ Type an IP or domain · tap for help",
        "cmd_ip": "Look up an IP address or domain",
        "cmd_help": "How to use the bot",
        "cmd_start": "Welcome message",
    },
    "ru": {
        "start": (
            WAVE_EMOJI + " Привет, {name}!\n\n"
            "Отправь мне <b>IP-адрес</b> или <b>домен</b>, и я покажу, где он находится, "
            "кто провайдер и многое другое.\n\nПримеры: {examples}\n\n"
            + CHAT_EMOJI + " Работаю и в любом чате: напиши <code>@{bot} 8.8.8.8</code>"
        ),
        "help": (
            "📚 <b>Как пользоваться</b>\n\n"
            "Просто отправь IP-адрес, домен или ссылку либо используй команду:\n\n"
            "/ip <code>&lt;адрес&gt;</code> - найти IP или домен\n"
            "/info <code>&lt;адрес&gt;</code> - то же, что /ip\n"
            "/start - приветствие\n"
            "/help - эта справка\n\n"
            "💬 <b>Инлайн-режим:</b> в любом чате напиши <code>@{bot} google.com</code> "
            "и выбери результат.\n\n"
            "⚙️ <b>Бот показывает:</b>\n"
            "• Точку на карте\n"
            "• Страну с флагом, регион, город и индекс\n"
            "• Часовой пояс с местным временем\n"
            "• Провайдера, организацию и AS\n"
            "• Имя хоста (PTR)\n"
            "• Регистратора и даты регистрации домена (WHOIS)\n"
            "• Признак мобильной сети"
        ),
        "need_address": "Укажи адрес после команды, например <code>/ip 8.8.8.8</code>\nПримеры: {examples}",
        "unknown_command": "🤖 Неизвестная команда. Смотри /help",
        "invalid_input": "❌ Это не похоже на IP-адрес или домен.\nПримеры: {examples}",
        "section_location": "Местоположение",
        "section_network": "Сеть",
        "local_time": "сейчас {time}",
        "continent": "Континент",
        "zip": "Индекс",
        "timezone": "Часовой пояс",
        "coords": "Координаты",
        "isp": "Провайдер",
        "org": "Организация",
        "as": "AS",
        "reverse": "Хост",
        "section_whois": "WHOIS",
        "domain": "Домен",
        "registrar": "Регистратор",
        "registered": "Зарегистрирован",
        "expires": "Истекает",
        "expired": "Истёк",
        "ago": "{duration} назад",
        "in": "через {duration}",
        "today": "сегодня",
        "date_format": "%d.%m.%Y",
        "tag_mobile": "📱 Мобильная сеть",
        "err_private": "Это адрес частной сети, у него нет публичного местоположения.",
        "err_reserved": "Это зарезервированный адрес, у него нет публичного местоположения.",
        "err_invalid": "Не удалось найти такой IP-адрес или домен.",
        "err_rate_limit": "Слишком много запросов. Попробуй через минуту.",
        "err_unavailable": "Сервис геолокации недоступен. Попробуй позже.",
        "err_unknown": "Не удалось выполнить запрос: {message}",
        "inline_hint": "ℹ️ Введи IP или домен · нажми для справки",
        "cmd_ip": "Найти IP-адрес или домен",
        "cmd_help": "Как пользоваться ботом",
        "cmd_start": "Приветствие",
    },
}

LANGUAGES = tuple(TEXTS)

UNITS = {
    "en": {"year": ("year", "years"), "month": ("month", "months"), "day": ("day", "days")},
    "ru": {"year": ("год", "года", "лет"), "month": ("месяц", "месяца", "месяцев"), "day": ("день", "дня", "дней")},
}


def get_lang(user):
    """Pick the interface language from the user's Telegram settings."""
    code = ((user.language_code if user else None) or "").lower()
    return "ru" if code.startswith("ru") else DEFAULT_LANG


def t(lang, key, **params):
    """Get a translated text, falling back to English."""
    text = TEXTS.get(lang, {}).get(key) or TEXTS[DEFAULT_LANG][key]
    return text.format(examples=EXAMPLES, **params)


def plural_ru(n, forms):
    """Russian plural: 1 год, 2 года, 5 лет, 11 лет, 21 год."""
    n = abs(n) % 100
    if 11 <= n <= 19:
        return forms[2]
    n %= 10
    if n == 1:
        return forms[0]
    if 2 <= n <= 4:
        return forms[1]
    return forms[2]


def format_duration(lang, days):
    """Rough human duration: 29 years / 3 месяца / 12 дней."""
    days = abs(days)
    for unit, size in (("year", 365), ("month", 30), ("day", 1)):
        if days >= size or unit == "day":
            count = days // size
            break

    forms = UNITS.get(lang, UNITS[DEFAULT_LANG])[unit]
    word = plural_ru(count, forms) if lang == "ru" else forms[0 if count == 1 else 1]
    return f"{count} {word}"
