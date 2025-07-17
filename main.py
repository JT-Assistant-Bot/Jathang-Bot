import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# ✅ Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://jthang-bot.onrender.com/webhook"  # Change if custom domain

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN is NOT set in Render environment variables!")

# ✅ Flask App
app = Flask(__name__)

# ✅ Telegram Bot Application
application = Application.builder().token(TOKEN).build()

# ✅ Handlers
async def start(update: Update, context):
    await update.message.reply_text("✅ Hello! Your bot is alive on Render!")

async def echo(update: Update, context):
    await update.message.reply_text(f"You said: {update.message.text}")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ✅ Flask Routes
@app.route("/", methods=["GET"])
def home():
    return "✅ Telegram bot is running on Render!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.get_event_loop().create_task(application.process_update(update))
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500
    return "OK", 200

# ✅ Start Telegram Bot
async def set_webhook():
    try:
        await application.bot.delete_webhook()  # Remove old webhook
        await application.bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"✅ Webhook set to: {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")

async def run_bot():
    await application.initialize()
    await application.start()
    await set_webhook()

# ✅ MAIN ENTRY POINT
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_bot())
    except Exception as e:
        logger.error(f"Webhook setup failed. Switching to polling... {e}")
        # ✅ Polling fallback if webhook fails
        loop.run_until_complete(application.run_polling())

    # ✅ Flask Server
    port = os.environ.get("PORT")
    if not port or not port.isdigit():
        port = 10000
    else:
        port = int(port)

    app.run(host="0.0.0.0", port=port)
