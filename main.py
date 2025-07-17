import os
import tempfile
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
import openai
import asyncio

# ✅ Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.environ.get("PORT", 8443))  # Render's dynamic port

openai.api_key = OPENAI_API_KEY

# ✅ Flask app for webhook
flask_app = Flask(__name__)
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# ✅ Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your assistant. How can I help you today?")

# ✅ Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can ask me anything or give a command!")

# ✅ Handle user message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = await get_ai_response(user_message)

    # Reply in text
    await update.message.reply_text(response)

    # Convert response to voice
    audio_file = text_to_voice(response)
    await update.message.reply_voice(voice=open(audio_file, 'rb'))

# ✅ OpenAI ChatGPT Response (new API)
async def get_ai_response(user_message: str) -> str:
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        chat_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Be concise and precise."},
                {"role": "user", "content": user_message}
            ]
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# ✅ Convert text to voice using gTTS
def text_to_voice(text):
    tts = gTTS(text=text, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        return fp.name

# ✅ Register bot handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("help", help_command))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ✅ Flask routes
@flask_app.route('/')
def home():
    return "Bot is running!"

@flask_app.route(f'/webhook/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    asyncio.run(bot_app.process_update(update))
    return "OK"

# ✅ Start Flask server with webhook
if __name__ == "__main__":
    print("Starting bot in Webhook mode...")
    from threading import Thread

    # Set Telegram webhook
    from telegram import Bot
    bot = Bot(token=TELEGRAM_TOKEN)
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook/{TELEGRAM_TOKEN}"
    bot.set_webhook(webhook_url)

    # Start Flask server
    flask_app.run(host="0.0.0.0", port=PORT)
