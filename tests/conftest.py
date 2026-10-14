import os
import sys
from pathlib import Path

# bot.py reads the token on import; tests never talk to Telegram
os.environ["BOT_TOKEN"] = "123456:TEST-TOKEN"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ipbot"))
