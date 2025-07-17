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

# ✅ /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello! Bot is LIVE on Render and fully working!")

application.add_handler(CommandHandler("start", start))

# ✅ Webhook endpoint
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, application.bot)

        # ✅ Create a new loop in the current thread and run the task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()

        return "OK", 200
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500

# ✅ Health check route
@app.route("/")
def index():
    return "🤖 Bot is alive on Render!", 200

# ✅ Startup
if __name__ == "__main__":
    # Reset webhook then set new one
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(application.bot.delete_webhook())
    webhook_url = "https://jthang-bot.onrender.com/webhook"
    loop.run_until_complete(application.bot.set_webhook(url=webhook_url))
    loop.close()

    logger.info(f"✅ Webhook set to: {webhook_url}")

    # Run Flask app
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
