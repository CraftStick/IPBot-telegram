# 🌍 IP Info Telegram Bot

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![Status](https://img.shields.io/badge/status-active-success)

A Telegram bot that reports your public IP address with detailed geolocation — country flag, city, ISP, timezone, and coordinates — all behind a few tappable buttons.

---

## 📑 Table of Contents

- [Features](#-features)
- [Preview](#-preview)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Technical Details](#️-technical-details)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact--links)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📍 **IP Detection** | Shows your current public IP |
| 🇺🇸 **Country + Flag** | Country name with emoji flag |
| 🏙️ **Location Details** | City, region, and timezone |
| 📡 **Network Info** | Internet Service Provider (ISP) |
| 🗺️ **Map Integration** | Open the location on OpenStreetMap / Google Maps |
| 🔄 **Real-time Refresh** | Re-fetch info anytime |
| 🎯 **Simple UX** | Inline buttons and plain commands |

---

## 📸 Preview

**Main interface**

```
👋 Hello, User!

Your current IP:  123.45.67.89
🇺🇸 Country:       United States
🏙️ City:           New York

Select an action:
[🔄 Refresh Info]  [📊 Full Details]
[📍 Show on Map]
```

**Full details**

```
📍 Your IP Information

🌐 IP Address:   123.45.67.89
🇺🇸 Country:      United States
🏙️ City:          New York
🗺️ Region:        New York
🕐 Timezone:      America/New_York
📡 ISP:           Comcast Cable
📍 Coordinates:   40.7128, -74.0060
🌍 Open in Google Maps
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python **3.7+**
- A Telegram account
- A bot token from [@BotFather](https://t.me/botfather)

### 2. Install

```bash
git clone https://github.com/CraftStick/IPBot-telegram.git
cd IPBot-telegram
pip install -r requirements.txt
```

### 3. Configure

```bash
cp config.example.py config.py
```

Open `config.py` and paste the token you got from [@BotFather](https://t.me/botfather):

```python
BOT_TOKEN = "123456:ABC-DEF..."
```

### 4. Run

```bash
python bot.py
```

---

## 📖 Usage

**Commands**

| Command | Description |
|---------|-------------|
| `/start` | Start the bot and show the main menu |
| `/info` | Get full IP information |
| `/help` | Show the help message |

**Buttons**

| Button | Action |
|--------|--------|
| 🔄 Refresh Info | Re-fetch IP data |
| 📊 Full Details | Extended information |
| 📍 Show on Map | Open location on a map |

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

`requirements.txt`:

```
pyTelegramBotAPI
requests
```

---

## 📁 Project Structure

```
IPBot-telegram/
├── bot.py              # Main bot application
├── requirements.txt    # Python dependencies
├── config.example.py   # Example configuration
├── README.md           # Documentation
└── .gitignore          # Git ignore rules
```

---

## 🐞 Troubleshooting

| Problem | Fix |
|---------|-----|
| `Unauthorized` on start | Token in `config.py` is wrong or missing |
| No response from `/start` | Check the bot is running and the machine has internet access |
| Geolocation is empty | You may have hit the ip-api rate limit — wait a minute |

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

