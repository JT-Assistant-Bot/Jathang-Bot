import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio
import logging
import httpx
from openai import AsyncOpenAI

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_OWNER_ID = os.getenv("BOT_OWNER_ID")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("❌ Missing TELEGRAM_TOKEN or OPENAI_API_KEY")

# OpenAI client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# FastAPI app
app = FastAPI()

# Telegram app
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Hello! I'm your AI assistant. Ask me anything!")

# Handle messages with OpenAI
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        # Generate AI response
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful Telegram assistant."},
                {"role": "user", "content": user_text}
            ]
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"⚠️ Error: {e}"

    await update.message.reply_text(reply)

# Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    logger.info("🚀 Starting Telegram bot with webhook...")
    await application.initialize()
    await application.start()
    url = os.getenv("RENDER_EXTERNAL_URL") + "/webhook"
    async with httpx.AsyncClient() as client:
        await client.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook", data={"url": url})
    logger.info("✅ Webhook set successfully.")

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
