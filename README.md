# 🌍 IP Info Telegram Bot

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![Status](https://img.shields.io/badge/status-active-success)

A Telegram bot that looks up any IP address or domain and shows its geolocation — country flag, city, ISP, AS, timezone, coordinates, and proxy/hosting flags — with one-tap map links.

> ℹ️ Telegram does not share users' IP addresses with bots, so the bot looks up the address you send it. To check your own IP, open [ifconfig.me](https://ifconfig.me) and send the result to the bot.

---

## 📑 Table of Contents

- [Features](#-features)
- [Preview](#-preview)
- [Quick Start](#-quick-start)
- [Docker](#-docker)
- [Usage](#-usage)
- [Tests](#-tests)
- [Technical Details](#️-technical-details)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact--links)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔎 **Any IP or domain** | IPv4, IPv6, domains (incl. IDN like `пример.рф`), URLs and `host:port` |
| 🇺🇸 **Country + Flag** | Country name with emoji flag |
| 🏙️ **Location Details** | City, region, ZIP code, continent, timezone with local time |
| 📡 **Network Info** | ISP, organization, AS and hostname (PTR) |
| 🌐 **WHOIS** | Registrar, registration and expiry dates of a domain (warns when it expires soon) |
| 🛡️ **Address Type** | Mobile network, proxy / VPN / Tor, hosting / data center flags |
| 🗺️ **Map** | An interactive Telegram map pin comes right above every card, plus OpenStreetMap / Google Maps / WHOIS links |
| 💬 **Inline Mode** | Type `@your_bot 8.8.8.8` in any chat and send the result card |
| 🇷🇺 **Two Languages** | English and Russian, picked from the user's Telegram language |
| ⚡ **Caching** | Repeated lookups are cached for 5 minutes to respect API limits |

---

## 📸 Preview

```
You: yandex.ru

[🗺️ Telegram map pin: Moscow, Russia · 77.88.55.88 · Yandex LLC]

🇷🇺 yandex.ru
77.88.55.88 · IPv4

📍 Location
┃ Moscow, Russia
┃ Continent: Europe
┃ ZIP code: 119021
┃ Timezone: Europe/Moscow (UTC+3), now 12:05
┃ Coordinates: 55.7558, 37.6173

📡 Network
┃ ISP: Yandex LLC
┃ AS: AS13238 (YANDEX)
┃ Hostname: yandex.ru

🌐 WHOIS
┃ Registrar: RU-CENTER-RU
┃ Registered: 1997-09-23 (29 years ago)
┃ Expires: 2027-10-01 (in 11 months)

┃ 🖥️ Hosting / data center

[🗺️ OpenStreetMap]  [🌍 Google Maps]
[🔎 WHOIS / BGP]
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python **3.9+**
- A Telegram account
- A bot token from [@BotFather](https://t.me/botfather)

### 2. Install

```bash
git clone https://github.com/CraftStick/IPBot-telegram.git
cd IPBot-telegram/ipbot
pip install -r requirements.txt
```

### 3. Configure

Either set an environment variable (recommended):

```bash
export BOT_TOKEN="123456:ABC-DEF..."
```

or create a config file:

```bash
cp config.example.py config.py
```

and paste the token you got from [@BotFather](https://t.me/botfather) into `config.py`. The `BOT_TOKEN` environment variable takes priority; `config.py` is git-ignored.

### 4. Run

```bash
python bot.py
```

### 5. Enable inline mode (optional)

In [@BotFather](https://t.me/botfather) send `/setinline`, choose your bot and enter a placeholder such as `IP address or domain`. After that `@your_bot 8.8.8.8` works in any chat.

---

## 🐳 Docker

```bash
cp .env.example .env   # put your token into .env
docker compose up -d --build
```

The image contains only the bot code; the token is passed through `.env` and the container restarts automatically.

---

## 📖 Usage

Just send the bot an IP address, domain, or link — or use a command:

| Command | Description |
|---------|-------------|
| `/ip <address>` | Look up an IP address or domain |
| `/info <address>` | Same as `/ip` |
| `/start` | Welcome message |
| `/help` | Show the help message |

Examples: `8.8.8.8`, `2606:4700::1111`, `google.com`, `https://github.com/CraftStick`

**Inline mode** — in any chat type `@your_bot google.com` and pick the result: a card with the IP info or a map pin.

The interface language (English / Russian) follows the user's Telegram language; country and city names are localized too.

For domains the card also shows **WHOIS** data: registrar, registration and expiry dates. It comes from [RDAP](https://about.rdap.org/) when the domain zone supports it, otherwise from classic WHOIS servers (port 43); for `.ru` / `.рф` / `.su` `whois.nic.ru` is used as a backup when the registry server is unreachable. Some zones (e.g. `.de`) don't publish these dates — then the section is skipped.

Private and reserved addresses (`192.168.x.x`, `10.x.x.x`, `127.0.0.1`, …) have no public location and are rejected.

---

## 🛠️ Technical Details

**API**

Powered by [ip-api.com](https://ip-api.com) — a free IP geolocation service.

- No API key required for basic usage
- Rate limit: **45 requests/minute** (per source IP)

**Dependencies**

| Package | Purpose |
|---------|---------|
| [`pyTelegramBotAPI`](https://pypi.org/project/pyTelegramBotAPI/) | Telegram Bot API wrapper |
| [`requests`](https://pypi.org/project/requests/) | HTTP client for API calls |
| [`tzdata`](https://pypi.org/project/tzdata/) | Timezone database for local time |

`requirements.txt`:

```
pyTelegramBotAPI==4.19.1
requests==2.32.3
tzdata==2024.2
```

---

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests don't need a bot token or network access: Telegram and ip-api are mocked.

---

## 📁 Project Structure

```
IPBot-telegram/
├── ipbot/
│   ├── bot.py              # Main bot application
│   ├── texts.py            # English and Russian texts
│   ├── domaininfo.py       # WHOIS / RDAP lookups
│   ├── config.example.py   # Example configuration
│   └── requirements.txt    # Python dependencies
├── tests/                  # pytest tests
├── Dockerfile
├── docker-compose.yml
├── .env.example            # Example environment file for Docker
├── requirements-dev.txt    # Dependencies for running tests
├── README.md               # Documentation
├── LICENSE                 # MIT License
└── .gitignore              # Git ignore rules
```

---

## 🐞 Troubleshooting

| Problem | Fix |
|---------|-----|
| `Bot token is not set` | Set `BOT_TOKEN` or create `config.py` from `config.example.py` |
| `Unauthorized` on start | The token is wrong — get a new one from @BotFather |
| No response from `/start` | Check the bot is running and the machine has internet access |
| `@your_bot` shows nothing in chats | Inline mode is off — enable it with `/setinline` in @BotFather |
| "Too many requests" | The ip-api limit (45 requests/minute for the whole bot) was hit — wait a minute |

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch — `git checkout -b feature/AmazingFeature`
3. Commit your changes — `git commit -m 'Add AmazingFeature'`
4. Push the branch — `git push origin feature/AmazingFeature`
5. Open a Pull Request

---

## 📄 License

Licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 📞 Contact & Links

- **GitHub:** [@CraftStick](https://github.com/CraftStick)
- **Repository:** [IPBot-telegram](https://github.com/CraftStick/IPBot-telegram)
- **Report Issues:** [GitHub Issues](https://github.com/CraftStick/IPBot-telegram/issues)

<div align="center">

---

Если было полезно — поставь ⭐, это очень помогает!

If you found this useful, consider leaving a ⭐ — it helps a lot!

</div>

