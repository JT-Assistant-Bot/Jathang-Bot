import os
import tempfile
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
import openai
import asyncio

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://jthang-bot.onrender.com

openai.api_key = OPENAI_API_KEY

# Flask app for webhook
flask_app = Flask(__name__)

# Telegram bot application
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your assistant. How can I help you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can ask me anything or give a command!")

# ✅ Handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = await get_ai_response(user_message)

    await update.message.reply_text(response)  # Send text
    audio_file = text_to_voice(response)      # Convert to voice
    await update.message.reply_voice(voice=open(audio_file, 'rb'))

# ✅ OpenAI GPT Response
async def get_ai_response(user_message: str) -> str:
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond concisely."},
                {"role": "user", "content": user_message}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ✅ Convert text to speech
def text_to_voice(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name

# ✅ Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ✅ Webhook route
@flask_app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.create_task(application.process_update(update))  # ✅ Safe async execution
    return "OK", 200

if __name__ == "__main__":
    asyncio.run(application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook"))
    print(f"Webhook set to: {WEBHOOK_URL}/webhook")
    flask_app.run(host="0.0.0.0", port=10000)
