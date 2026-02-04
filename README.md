
# 🌍 IP Info Telegram Bot

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue)
![Status](https://img.shields.io/badge/status-active-success)

A Telegram bot that shows your public IP address with detailed location information including country flags, city, ISP, and coordinates.

## ✨ Features

| Feature | Description |
|---------|-------------|
| **📍 IP Address Detection** | Shows your current public IP |
| **🇺🇸 Country with Flag** | Country name with emoji flag (🇺🇸, 🇷🇺, 🇪🇺, etc.) |
| **🏙️ Location Details** | City, region, timezone information |
| **📡 Network Info** | Internet Service Provider (ISP) details |
| **🗺️ Map Integration** | Show location on OpenStreetMap |
| **🔄 Real-time Updates** | Refresh information anytime |
| **🎯 User-friendly** | Simple buttons and intuitive commands |

## 📸 Screenshots

### Main Interface
👋 Hello, User!

Your current IP: 123.45.67.89
🇺🇸 Country: United States
🏙️ City: New York

Select an action:
[🔄 Refresh Info] [📊 Full Details]
[📍 Show on Map]

### Full Details
📍 Your IP Information:

- 🌐 IP Address: 123.45.67.89
- 🇺🇸 Country: United States
- 🏙️ City: New York
- 🗺️ Region: New York
- 🕐 Timezone: America/New_York
- 📡 ISP: Comcast Cable
- 📍 Coordinates: 40.7128, -74.0060
- 🌍 Open in Google Maps

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.7 or higher
- Telegram account
- Bot token from [@BotFather](https://t.me/botfather)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/CraftStick/IPBot-telegram.git
cd IPBot-telegram

# Install dependencies
pip install -r requirements.txt
3. Configuration
bash
# Copy example config
cp config.example.py config.py

# Edit config.py and add your bot token
# Get your token from @BotFather on Telegram
4. Run the Bot
bash
python bot.py
📖 Usage
Commands
Command	Description
/start	Start the bot and show main menu
/info	Get full IP information
/help	Show help message
Buttons
Button	Action
- 🔄 Refresh Info	Update IP data
- 📊 Full Details	Extended information
- 📍 Show on Map	Open location on map
- 🛠️ Technical Details
API Used
ip-api.com - Free IP geolocation service

Rate limit: 45 requests per minute

No API key required for basic usage

Dependencies
pyTelegramBotAPI - Telegram Bot API wrapper

requests - HTTP library for API calls

Installation via pip
bash
pip install pyTelegramBotAPI requests
📁 Project Structure
text
IPBot-telegram/
├── bot.py              # Main bot application
├── requirements.txt    # Python dependencies
├── config.example.py   # Example configuration
├── README.md          # Documentation
└── .gitignore         # Git ignore rules
🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

Fork the repository

Create your feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

⭐ Support
If you find this project useful, please give it a star on GitHub!

📞 Contact & Links
GitHub: CraftStick

Repository: IPBot-telegram

Report Issues: GitHub Issues

