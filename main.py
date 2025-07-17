import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise ValueError("❌ BOT_TOKEN or RENDER_EXTERNAL_URL is not set!")

# ✅ Flask App
app = Flask(__name__)

# ✅ Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive on Render!")

application.add_handler(CommandHandler("start", start))

# ✅ Create a dedicated event loop for PTB
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def run_bot():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    logger.info(f"✅ Webhook set to: {WEBHOOK_URL}/webhook")
    await application.updater.start_polling()  # Keep background jobs alive

# ✅ Run the bot in the background
loop.create_task(run_bot())

# ✅ Start the event loop in a background thread
import threading
threading.Thread(target=loop.run_forever, daemon=True).start()

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run_coroutine_threadsafe(application.process_update(update), loop)
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot is running on Render!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
