import os
import tempfile
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
from openai import OpenAI

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not RENDER_EXTERNAL_URL:
    raise ValueError("Missing required environment variables!")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize Telegram Application
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Webhook URL
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}/webhook"

# Flask app
app = Flask(__name__)

# ----------------- COMMAND HANDLERS -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your AI Assistant. How can I help you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can ask me anything or give a command!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response_text = get_ai_response(user_message)

    # Send text response
    await update.message.reply_text(response_text)

    # Convert to voice and send
    audio_file = text_to_voice(response_text)
    await update.message.reply_voice(voice=open(audio_file, 'rb'))

# ----------------- AI RESPONSE -----------------
def get_ai_response(user_message: str) -> str:
    try:
        completion = client.responses.create(
            model="gpt-4.1-mini",
            input=f"You are a helpful assistant. Respond concisely.\nUser: {user_message}\nAssistant:"
        )
        return completion.output_text
    except Exception as e:
        return f"Error: {str(e)}"

# ----------------- TEXT TO VOICE -----------------
def text_to_voice(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name

# ----------------- FLASK ROUTES -----------------
@app.route('/')
def home():
    return "Bot is live on Render!"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "OK", 200

# ----------------- MAIN -----------------
if __name__ == "__main__":
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Set webhook
    async def run():
        await application.bot.set_webhook(WEBHOOK_URL)
        print(f"Webhook set to: {WEBHOOK_URL}")

    import asyncio
    asyncio.get_event_loop().run_until_complete(run())

    # Start Flask server
    app.run(host="0.0.0.0", port=10000)
