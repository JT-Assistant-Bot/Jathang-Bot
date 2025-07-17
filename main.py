import os
import tempfile
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
from openai import OpenAI

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-service.onrender.com")

client = OpenAI(api_key=OPENAI_API_KEY)

# Flask app
app = Flask(__name__)

# Telegram bot application
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your assistant. How can I help you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can ask me anything or give a command!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = get_ai_response(user_message)

    # Reply in text
    await update.message.reply_text(response)

    # Convert response to voice
    audio_file = text_to_voice(response)
    await update.message.reply_voice(voice=open(audio_file, 'rb'))

def get_ai_response(user_message: str) -> str:
    try:
        completion = client.responses.create(
            model="gpt-4.1-mini",
            input=f"You are a helpful assistant. Respond concisely.\nUser: {user_message}\nAssistant:"
        )
        return completion.output_text
    except Exception as e:
        return f"Error: {str(e)}"

def text_to_voice(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name

# Add handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Flask route for Telegram webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.update_queue.put_nowait(update)
    return "OK", 200

@app.route("/")
def home():
    return "Bot is running with Webhook!", 200

if __name__ == "__main__":
    import asyncio
    from telegram import Bot

    bot = Bot(token=TELEGRAM_TOKEN)
    webhook_url = f"{BASE_URL}/webhook"

    # Set webhook
    asyncio.get_event_loop().run_until_complete(bot.set_webhook(webhook_url))

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
