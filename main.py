import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ========================
#  CONFIG
# ========================
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render provides this automatically

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is NOT set! Go to Render → Environment and add it.")

if not WEBHOOK_URL:
    raise ValueError("❌ RENDER_EXTERNAL_URL is NOT set! Render should provide this automatically.")

# Logging for debugging
logging.basicConfig(level=logging.INFO)

# ========================
#  FLASK APP
# ========================
app = Flask(__name__)

# ========================
#  TELEGRAM APP
# ========================
application = Application.builder().token(TOKEN).build()

# Simple command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is live on Render!")

application.add_handler(CommandHandler("start", start))

# ========================
#  WEBHOOK ROUTE
# ========================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        application.create_task(application.process_update(update))  # Correct async handling
        return "OK", 200
    except Exception as e:
        logging.error(f"Error in webhook: {e}")
        return "ERROR", 500

@app.route("/")
def home():
    return "✅ Telegram Bot is running on Render!", 200

# ========================
#  STARTUP: SET WEBHOOK
# ========================
async def set_webhook():
    url = f"{WEBHOOK_URL}/webhook"
    await application.bot.set_webhook(url=url)
    logging.info(f"✅ Webhook set to: {url}")

if __name__ == "__main__":
    import asyncio

    # Run webhook setter
    asyncio.run(set_webhook())

    # Start Flask app
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
