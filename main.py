import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import httpx

# ✅ Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing!")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing!")

# ✅ Initialize FastAPI & Telegram Bot
app = FastAPI()
application = Application.builder().token(TELEGRAM_TOKEN).build()

# ✅ OpenAI API endpoint
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive on Render!")

# ✅ AI Response for any text
async def ai_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.7
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(OPENAI_URL, headers=HEADERS, json=payload)
        ai_text = response.json()["choices"][0]["message"]["content"]

    await update.message.reply_text(ai_text)

# ✅ Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_response))

# ✅ Webhook route
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}

# ✅ Set webhook on startup
@app.on_event("startup")
async def on_startup():
    url = "https://jthang-bot.onrender.com/webhook"
    await application.bot.set_webhook(url)
    logger.info(f"✅ Webhook set: {url}")
