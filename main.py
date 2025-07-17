import os
import json
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")  # Render gives this automatically

# Create bot application
application = Application.builder().token(TOKEN).build()

# Simple start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am alive on Render!")

application.add_handler(CommandHandler("start", start))

# Flask app
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running on Render!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))  # ✅ Correct way
    except Exception as e:
        print(f"Error in webhook: {e}")
    return "OK", 200

if __name__ == "__main__":
    # ✅ Set webhook AFTER app is ready
    async def set_webhook():
        if WEBHOOK_URL:
            url = f"{WEBHOOK_URL}/webhook"
            await application.bot.set_webhook(url=url)
            print(f"Webhook set to: {url}")
        else:
            print("WEBHOOK_URL not set!")

    asyncio.run(set_webhook())
    # ✅ Start Flask app
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
