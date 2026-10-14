FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY ipbot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the code: the token comes from the BOT_TOKEN env variable, never from config.py
COPY ipbot/bot.py ipbot/texts.py ipbot/domaininfo.py ./

RUN useradd --create-home --uid 1000 bot
USER bot

CMD ["python", "bot.py"]
