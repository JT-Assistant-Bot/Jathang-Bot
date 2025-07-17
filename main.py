import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import openai

# ✅ Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is NOT set!")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is NOT set!")

openai.api_key = OPENAI_API_KEY

# ✅ Create Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# ✅ Flask App
app = Flask(__name__)

# ✅ Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Hello! I'm your AI Assistant. Ask me anything!")

async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        # ✅ Call OpenAI GPT API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or gpt-4 if you have access
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        ai_reply = response['choices'][0]['message']['content']
        await update.message.reply_text(ai_reply)
    except Exception as e:
        await update.message.reply_text("⚠️ Error processing your request.")
        logger.error(f"OpenAI API Error: {e}")

# ✅ Add Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))

# ✅ Flask Routes
@app.route("/")
def home():
    return "✅ Telegram AI Bot is Running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        asyncio.run(application.process_update(update))  # ✅ Fix for Flask async
        return "OK", 200
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
        return "ERROR", 500

if __name__ == "__main__":
    # ✅ Set webhook before starting Flask
    asyncio.run(application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook"))
    logger.info(f"✅ Webhook set to: {WEBHOOK_URL}/webhook")

    # ✅ Run Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
