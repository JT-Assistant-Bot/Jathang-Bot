import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set!")

# Create Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Your bot is alive on Render!")

application.add_handler(CommandHandler("start", start))

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_data = request.get_json()
        update = Update.de_json(update_data, application.bot)

        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()

        return "OK", 200
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500

if __name__ == "__main__":
    # Remove old webhook and set new one
    async def init_bot():
        await application.bot.delete_webhook()
        webhook_url = "https://jthang-bot.onrender.com/webhook"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"✅ Webhook set to: {webhook_url}")

    asyncio.run(init_bot())

    # Start Flask server
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
