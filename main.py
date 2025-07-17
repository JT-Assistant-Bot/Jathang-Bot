import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is NOT set!")

WEBHOOK_URL = "https://jthang-bot.onrender.com/webhook"

app = Flask(__name__)

# Create Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# Handlers
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is working! 🎉")

async def echo(update: Update, context):
    await update.message.reply_text(f"You said: {update.message.text}")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Initialize the event loop for Application
loop = asyncio.get_event_loop()
loop.create_task(application.initialize())
loop.create_task(application.start())

@app.route("/")
def home():
    return "✅ Telegram Bot Running on Render!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        update = Update.de_json(data, application.bot)
        asyncio.run_coroutine_threadsafe(application.process_update(update), loop)
        return "OK", 200
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500

if __name__ == "__main__":
    # Set webhook
    asyncio.run(application.bot.set_webhook(WEBHOOK_URL))
    app.run(host="0.0.0.0", port=10000)
