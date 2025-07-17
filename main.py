import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ✅ Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Load environment variables
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN is NOT set!")
if not WEBHOOK_URL:
    raise ValueError("❌ RENDER_EXTERNAL_URL is NOT set!")

# ✅ Initialize Flask
app = Flask(__name__)

# ✅ Create Telegram Application
application = Application.builder().token(TOKEN).build()

# ✅ Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello! Your bot is working on Render!")

application.add_handler(CommandHandler("start", start))

# ✅ Flask route for Telegram webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        # Process update asynchronously
        application.create_task(application.process_update(update))
        return "OK", 200
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500

# ✅ Flask route for health check
@app.route("/")
def home():
    return "Bot is running!", 200

# ✅ Start Flask and set webhook
if __name__ == "__main__":
    import asyncio

    async def set_webhook():
        await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
        logger.info(f"✅ Webhook set to: {WEBHOOK_URL}/webhook")

    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
