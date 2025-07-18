import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio
from openai import AsyncOpenAI

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing!")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing!")

# Initialize OpenAI
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# FastAPI app
app = FastAPI()

# Telegram Bot Application
application = Application.builder().token(TELEGRAM_TOKEN).build()


# ✅ /start command
async def start(update: Update, context):
    await update.message.reply_text("✅ Hello! I’m your AI Assistant. Send me any text and I’ll reply.")

# ✅ Handle all text messages
async def handle_message(update: Update, context):
    user_text = update.message.text
    await update.message.reply_text("🤔 Thinking...")

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": user_text},
            ],
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        ai_reply = f"❌ Error: {str(e)}"

    await update.message.reply_text(ai_reply)


# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ✅ FastAPI endpoint for webhook
@app.post("/webhook")
async def webhook(req: Request):
    try:
        data = await req.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
    return JSONResponse({"status": "ok"})


# ✅ Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting Telegram bot with webhook...")
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(url="https://jthang-bot.onrender.com/webhook")
    logger.info("✅ Webhook set successfully.")


# ✅ Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
    await application.shutdown()
