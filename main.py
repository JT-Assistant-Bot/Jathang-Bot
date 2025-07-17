import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ========================
#  CONFIG
# ========================
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is NOT set!")
if not WEBHOOK_URL:
    raise ValueError("❌ RENDER_EXTERNAL_URL is NOT set!")

logging.basicConfig(level=logging.INFO)

# Flask app
app = Flask(__name__)

# Telegram Application
application = Application.builder().token(TOKEN).build()

# ========================
#  COMMAND HANDLER
# ========================
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

        # Run inside event loop
        asyncio.run(application.process_update(update))

        return "OK", 200
    except Exception as e:
        logging.error(f"Error in webhook: {e}")
        return "ERROR", 500

@app.route("/")
def home():
    return "✅ Telegram Bot is running on Render!", 200

# ========================
#  SET WEBHOOK & RUN FLASK
# ========================
async def set_webhook():
    url = f"{WEBHOOK_URL}/webhook"
    await application.bot.set_webhook(url=url)
    logging.info(f"✅ Webhook set to: {url}")

if __name__ == "__main__":
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
