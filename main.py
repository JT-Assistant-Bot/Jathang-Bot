import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = f"https://jthang-bot.onrender.com/webhook"

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN is NOT set in environment variables!")

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram Application
application = Application.builder().token(TOKEN).build()


# ✅ Command handler for /start
async def start(update: Update, context):
    await update.message.reply_text("✅ Hello! Your bot is alive on Render! 🎉")


# ✅ Message handler for any text
async def echo(update: Update, context):
    await update.message.reply_text(f"You said: {update.message.text}")


# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


@app.route("/", methods=["GET"])
def home():
    return "✅ Telegram bot is running on Render!"


@app.route("/webhook", methods=["POST"])
async def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500
    return "OK", 200


async def set_webhook():
    await application.bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"✅ Webhook set to: {WEBHOOK_URL}")


async def run_bot():
    await application.initialize()
    await application.start()
    await set_webhook()


if __name__ == "__main__":
    # Start the bot asynchronously before Flask runs
    asyncio.get_event_loop().run_until_complete(run_bot())

    # ✅ Fix port issue for Render
    port = os.environ.get("PORT")
    if not port or not port.isdigit():
        port = 10000
    else:
        port = int(port)

    app.run(host="0.0.0.0", port=port)
