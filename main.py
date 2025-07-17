import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
import tempfile
from openai import OpenAI

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")

client = OpenAI(api_key=OPENAI_API_KEY)

# Flask app
app = Flask(__name__)

# Telegram bot app
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your assistant. How can I help you?")

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = get_ai_response(user_message)
    await update.message.reply_text(response)

    # Convert to voice
    audio_file = text_to_voice(response)
    await update.message.reply_voice(voice=open(audio_file, 'rb'))

# AI Response using OpenAI new API
def get_ai_response(user_message: str) -> str:
    try:
        completion = client.responses.create(
            model="gpt-4.1-mini",
            input=f"You are a helpful assistant. Be concise.\nUser: {user_message}\nAssistant:"
        )
        return completion.output_text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Text to Voice
def text_to_voice(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name

# Add handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask route for Telegram webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    asyncio.run(bot_app.update_queue.put(Update.de_json(data, bot_app.bot)))
    return "ok", 200

# Home route
@app.route("/", methods=["GET"])
def home():
    return "Bot is live!", 200

async def set_webhook():
    webhook_url = f"{RENDER_URL}/webhook"
    await bot_app.bot.set_webhook(webhook_url)
    print(f"Webhook set to: {webhook_url}")

if __name__ == "__main__":
    asyncio.run(set_webhook())
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
