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
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Your Render URL (we will set this)

client = OpenAI(api_key=OPENAI_API_KEY)

app_flask = Flask(__name__)

# Telegram Bot setup
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your assistant. How can I help you today?")

# ✅ Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can ask me anything or give a command!")

# ✅ Handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = get_ai_response(user_message)

    await update.message.reply_text(response)

    audio_file = text_to_voice(response)
    await update.message.reply_voice(voice=open(audio_file, 'rb'))

# ✅ OpenAI response
def get_ai_response(user_message: str) -> str:
    try:
        completion = client.responses.create(
            model="gpt-4.1-mini",
            input=f"You are a helpful assistant. Respond concisely.\nUser: {user_message}\nAssistant:"
        )
        return completion.output_text
    except Exception as e:
        return f"Error: {str(e)}"

# ✅ Text to Voice using gTTS
def text_to_voice(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name

# ✅ Add Telegram handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ✅ Flask route for Telegram webhook
@app_flask.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

# ✅ Set webhook when server starts
@app_flask.before_first_request
def set_webhook():
    application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")

if __name__ == "__main__":
    app_flask.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
