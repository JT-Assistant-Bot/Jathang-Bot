import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import httpx

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing!")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing!")

# FastAPI app
app = FastAPI()

# Telegram bot application
application = Application.builder().token(TELEGRAM_TOKEN).build()

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is alive and ready!")

# Respond to all other messages with OpenAI
async def chat_with_openai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    logger.info(f"User message: {user_message}")

    try:
        # Call OpenAI API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_message}
                    ]
                }
            )
            data = response.json()
            ai_reply = data["choices"][0]["message"]["content"]

        await update.message.reply_text(ai_reply)

    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        await update.message.reply_text("⚠️ Sorry, something went wrong.")

# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_openai))

# Webhook setup
@app.on_event("startup")
async def startup():
    url = "https://jthang-bot.onrender.com/webhook"
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url)
    logger.info(f"✅ Webhook set: {url}")

@app.on_event("shutdown")
async def shutdown():
    await application.stop()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    await application.update_queue.put(Update.de_json(data, application.bot))
    return {"status": "ok"}
