import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ✅ Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Flask app
app = Flask(__name__)

# ✅ Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is NOT set!")

# ✅ Telegram Bot Application
application = Application.builder().token(BOT_TOKEN).build()

# ✅ Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello! Your bot is LIVE on Render!")

# ✅ Add handler
application.add_handler(CommandHandler("start", start))

# ✅ Webhook route
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, application.bot)

        # Fix: Run the async handler in a fresh loop per request
        asyncio.run(application.process_update(update))

        return "OK", 200
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500

# ✅ Health check route
@app.route("/")
def index():
    return "🤖 Bot is alive on Render!", 200

# ✅ Start Flask + set webhook
if __name__ == "__main__":
    # Delete any old webhook and set new one
    asyncio.run(application.bot.delete_webhook())
    webhook_url = f"https://jthang-bot.onrender.com/webhook"
    asyncio.run(application.bot.set_webhook(url=webhook_url))
    logger.info(f"✅ Webhook set to: {webhook_url}")

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
