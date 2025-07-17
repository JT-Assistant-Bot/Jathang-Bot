import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is NOT set!")

# Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# Bot command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is LIVE and working on Render!")

application.add_handler(CommandHandler("start", start))

# Webhook route (sync, but runs async inside)
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, application.bot)

        # ✅ Create and run a temporary event loop for this request
        asyncio.run(application.process_update(update))

        return "OK", 200
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500

@app.route("/")
def index():
    return "🤖 Bot is alive!", 200

if __name__ == "__main__":
    # Delete old webhook and set new one
    async def setup_webhook():
        await application.bot.delete_webhook()
        await application.bot.set_webhook("https://jthang-bot.onrender.com/webhook")

    asyncio.run(setup_webhook())

    logger.info("✅ Webhook set successfully!")

    # Run Flask
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
