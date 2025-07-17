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

# ✅ Telegram Bot Application
application = Application.builder().token(BOT_TOKEN).build()

# ✅ Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and working on Render!")

application.add_handler(CommandHandler("start", start))

# ✅ Event Loop
loop = asyncio.get_event_loop()

async def init_bot():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    logger.info(f"✅ Webhook set to: {WEBHOOK_URL}/webhook")

# ✅ Run initialization in loop
loop.run_until_complete(init_bot())

# ✅ Webhook route
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
