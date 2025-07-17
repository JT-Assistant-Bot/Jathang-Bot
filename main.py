import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from openai import AsyncOpenAI

# ---------------------------
# CONFIG
# ---------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = f"https://jthang-bot.onrender.com/webhook"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# OpenAI Client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Telegram Application
application = ApplicationBuilder().token(TOKEN).build()


# ---------------------------
# HANDLERS
# ---------------------------
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is alive on Render! Ask me anything.")

async def handle_message(update: Update, context):
    user_message = update.message.text
    try:
        # Call OpenAI API
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Use your model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
        )
        reply = response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        reply = "⚠️ Sorry, I couldn't process that."

    await update.message.reply_text(reply)


# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ---------------------------
# WEBHOOK
# ---------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run_coroutine_threadsafe(application.process_update(update), application.loop)
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "Error", 500
    return "OK", 200


@app.route("/", methods=["GET"])
def home():
    return "✅ Telegram Bot running with Flask + OpenAI!"


# ---------------------------
# STARTUP
# ---------------------------
if __name__ == "__main__":
    # Initialize bot
    async def run():
        await application.initialize()
        await application.start()
        await application.bot.delete_webhook()
        await application.bot.set_webhook(WEBHOOK_URL)

    asyncio.get_event_loop().run_until_complete(run())

    # Start Flask server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
