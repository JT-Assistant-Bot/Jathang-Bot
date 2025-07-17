import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler

# ---------------- Logging -----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Config ------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is NOT set!")

WEBHOOK_URL = "https://jthang-bot.onrender.com/webhook"  # Replace with your Render URL

# ---------------- Flask App ----------------
app = Flask(__name__)

# ---------------- Telegram Bot ----------------
application = Application.builder().token(BOT_TOKEN).build()

# /start command
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is alive and working!")

application.add_handler(CommandHandler("start", start))

# ---------------- Async Initialization ----------------
async def init_telegram():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook set to: {WEBHOOK_URL}")

# Start the bot on event loop
loop = asyncio.get_event_loop()
loop.run_until_complete(init_telegram())

# ---------------- Flask Routes ----------------
@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is alive on Render!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run_coroutine_threadsafe(application.update_queue.put(update), loop)
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500
    return "OK", 200

# ---------------- Run Flask ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
