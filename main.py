import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== BOT CONFIGURATION ===================
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set in Render Environment Variables
OWNER_ID = 5927345569  # Replace with your Telegram ID
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")  # Example: https://jthang-bot.onrender.com
PORT = int(os.environ.get("PORT", 10000))

# ================== FLASK APP ===================
app = Flask(__name__)

# ================== TELEGRAM APP ===================
application = Application.builder().token(TOKEN).build()

# ================== COMMAND HANDLERS ===================
async def start(update: Update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Access Denied ❌")
        return
    await update.message.reply_text("✅ Hello JT! Your bot is live on Render 🚀")

async def echo(update: Update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Access Denied ❌")
        return
    await update.message.reply_text(f"Echo: {update.message.text}")

# Add Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# ================== WEBHOOK ROUTE ===================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        asyncio.run(application.process_update(update))  # ✅ Fixed issue
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
    return "OK", 200

# ================== START SERVER & SET WEBHOOK ===================
if __name__ == "__main__":
    async def set_webhook():
        url = f"{WEBHOOK_URL}/webhook"
        await application.bot.set_webhook(url=url)
        logger.info(f"Webhook set to: {url}")

    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=PORT)
