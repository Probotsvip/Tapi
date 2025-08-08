import os

# MongoDB Configuration
MONGO_DB_URI = "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority"

# Telegram Configuration
TELEGRAM_BOT_TOKEN = "7322756571:AAEi5MzxijBu7czGyx-bP8EsoztVfHaGqsw"
TELEGRAM_CHANNEL_ID = "-1002863131570"

# App Configuration
SECRET_KEY = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")