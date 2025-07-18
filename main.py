import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from openai import OpenAI
from pydub import AudioSegment
import speech_recognition as sr
from datetime import datetime

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "5927345569"))  # Replace with your ID

# OpenAI client
client = OpenAI(api_key=OPENAI_KEY)

# Create FastAPI app
app = FastAPI()

# Build Telegram app
telegram_app = ApplicationBuilder().token(TOKEN).build()

# ✅ Add startup event to initialize Telegram app
@app.on_event("startup")
async def on_startup():
    await telegram_app.initialize()
    await telegram_app.start()
    # ✅ Set webhook
    url = "https://jthang-bot.onrender.com/webhook"
    await telegram_app.bot.set_webhook(url)
    logger.info(f"✅ Webhook set successfully at {url}")

@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.stop()
    await telegram_app.shutdown()

# Handlers
async def start(update, context):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    await update.message.reply_text("✅ Private Bot Active!")

async def chatgpt_handler(update, context):
    if update.effective_user.id != ALLOWED_USER_ID:
        return
    user_text = update.message.text
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": user_text}]
    )
    reply = response.choices[0].message.content
    await update.message.reply_text(reply)
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    ogg_path = "voice.ogg"
    wav_path = "voice.wav"

    await file.download_to_drive(ogg_path)

    # Convert OGG to WAV
    AudioSegment.from_ogg(ogg_path).export(wav_path, format="wav")

    # Recognize speech
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            text = "Sorry, I couldn't understand the audio."

    # If user asks for time
    if "time" in text.lower():
        now = datetime.now().strftime("%H:%M:%S")
        await update.message.reply_text(f"The current time is {now}")
    else:
        await update.message.reply_text(f"You said: {text}")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chatgpt_handler))
telegram_app.add_handler(MessageHandler(filters.VOICE, handle_voice))

# ✅ Webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
