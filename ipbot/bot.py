import telebot
from telebot import types
import requests
import time
import os

# Try to import from config, otherwise use placeholder
try:
    from config import BOT_TOKEN
    TOKEN = BOT_TOKEN
except ImportError:
    # For GitHub/public version, use placeholder
    TOKEN = "YOUR_BOT_TOKEN_HERE"
    print("⚠️  Warning: Using placeholder token. Create config.py with your actual token.")

bot = telebot.TeleBot(TOKEN)
def get_emoji_flag(country_code):
    """Convert country code to emoji flag."""
    if not country_code or len(country_code) != 2:
        return "🏳️"
    
    # Convert country code to emoji flag
    # 'A' -> U+1F1E6, 'B' -> U+1F1E7, etc.
    emoji = ''.join(chr(ord(ch) + 127397) for ch in country_code.upper())
    return emoji

def get_ip_info():
    """Get complete IP address information."""
    try:
        # Using ip-api.com (free, up to 45 requests per minute)
        response = requests.get('http://ip-api.com/json/', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'success':
            return {
                'ip': data.get('query', 'Not defined'),
                'country': data.get('country', 'Not defined'),
                'country_code': data.get('countryCode', ''),
                'city': data.get('city', 'Not defined'),
                'region': data.get('regionName', 'Not defined'),
                'isp': data.get('isp', 'Not defined'),
                'timezone': data.get('timezone', 'Not defined'),
                'latitude': data.get('lat'),
                'longitude': data.get('lon'),
                'flag': get_emoji_flag(data.get('countryCode'))
            }
        else:
            return None
    except Exception as e:
        print(f"Error getting IP info: {e}")
        return None

def format_ip_info(info):
    """Format IP information into a beautiful text."""
    if not info:
        return "❌ Could not get IP information"
    
    # Main information
    result = f"""
📍 **Your IP Information:**

**🌐 IP Address:** `{info['ip']}`
{info.get('flag', '🏳️')} **Country:** {info['country']}
🏙️ **City:** {info['city']}
🗺️ **Region:** {info['region']}
🕐 **Timezone:** {info['timezone']}
📡 **ISP:** {info['isp']}
"""
    
    # Add coordinates if available
    if info.get('latitude') and info.get('longitude'):
        result += f"""📍 **Coordinates:** {info['latitude']}, {info['longitude']}
🌍 [Open in Google Maps](https://maps.google.com/?q={info['latitude']},{info['longitude']})"""
    
    return result

# ========================================
# /start COMMAND
# ========================================
@bot.message_handler(commands=['start'])
def start_command(message):
    info = get_ip_info()
    
    # Create keyboard with buttons
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_refresh = types.KeyboardButton("🔄 Refresh Info")
    btn_details = types.KeyboardButton("📊 Full Details")
    btn_map = types.KeyboardButton("📍 Show on Map")
    markup.add(btn_refresh, btn_details, btn_map)
    
    if info:
        response_text = (
            f"👋 Hello, {message.from_user.first_name}!\n\n"
            f"**Your current IP:** `{info['ip']}`\n"
            f"{info['flag']} **Country:** {info['country']}\n"
            f"🏙️ **City:** {info['city']}\n\n"
            "Select an action:"
        )
    else:
        response_text = f"👋 Hello, {message.from_user.first_name}!\n\nCould not get IP information. Try refreshing."
    
    bot.send_message(
        message.chat.id,
        response_text,
        reply_markup=markup,
        parse_mode='Markdown'
    )

# ========================================
# "🔄 Refresh Info" BUTTON HANDLER
# ========================================
@bot.message_handler(func=lambda message: message.text == "🔄 Refresh Info")
def handle_refresh_ip(message):
    info = get_ip_info()
    
    if info:
        response_text = (
            f"✅ Information updated!\n\n"
            f"**IP:** `{info['ip']}`\n"
            f"{info['flag']} **Country:** {info['country']}\n"
            f"🏙️ **City:** {info['city']}"
        )
    else:
        response_text = "❌ Could not get IP information. Try again later."
    
    bot.send_message(
        message.chat.id,
        response_text,
        parse_mode='Markdown'
    )

# ========================================
# "📊 Full Details" BUTTON HANDLER
# ========================================
@bot.message_handler(func=lambda message: message.text == "📊 Full Details")
def handle_details(message):
    info = get_ip_info()
    
    if info:
        response_text = format_ip_info(info)
    else:
        response_text = "❌ Could not get detailed IP information."
    
    bot.send_message(
        message.chat.id,
        response_text,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# ========================================
# "📍 Show on Map" BUTTON HANDLER
# ========================================
@bot.message_handler(func=lambda message: message.text == "📍 Show on Map")
def handle_map(message):
    info = get_ip_info()
    
    if info and info.get('latitude') and info.get('longitude'):
        lat, lon = info['latitude'], info['longitude']
        map_url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=12/{lat}/{lon}"
        
        response_text = (
            f"📍 **Location on map:**\n\n"
            f"**IP:** `{info['ip']}`\n"
            f"**City:** {info['city']}, {info['country']}\n"
            f"**Coordinates:** {lat}, {lon}\n\n"
            f"[🗺️ Open map]({map_url})"
        )
    else:
        response_text = "❌ Could not get coordinates to show on map."
    
    bot.send_message(
        message.chat.id,
        response_text,
        parse_mode='Markdown',
        disable_web_page_preview=False
    )

# ========================================
# TEXT COMMANDS HANDLERS
# ========================================
@bot.message_handler(commands=['info'])
def info_command(message):
    """Full information with /info command"""
    info = get_ip_info()
    
    if info:
        response_text = format_ip_info(info)
    else:
        response_text = "❌ Could not get IP information."
    
    bot.send_message(
        message.chat.id,
        response_text,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    """Show help message"""
    help_text = """
📚 **Available Commands:**

/start - Start the bot
/info - Get full IP information
/help - Show this message

🎯 **Buttons:**
🔄 Refresh Info - Update IP data
📊 Full Details - Extended information
📍 Show on Map - Open location on map

⚙️ **Bot shows:**
• IP address
• Country with flag emoji
• City and region
• Internet provider
• Timezone
• Coordinates
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# ========================================
# HANDLE OTHER TEXT MESSAGES
# ========================================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Handle all other text messages"""
    if message.text not in ["🔄 Refresh Info", "📊 Full Details", "📍 Show on Map"]:
        bot.reply_to(
            message,
            "🤖 Use buttons below or commands:\n/start - start\n/info - full info\n/help - help"
        )

# ========================================
# BOT STARTUP
# ========================================
if __name__ == '__main__':
    print("🤖 Bot started and waiting for /start command...")
    print("📡 Bot shows: IP, country with flag, city, and more details")
    
    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=30
            )
        except Exception as e:
            print(f"⚠️ Error: {e}")
            print("🔄 Restarting in 10 seconds...")
            time.sleep(10)