import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from openai import AsyncOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Debug: log environment status (don't log actual secrets!)
logger.info(f"Environment check: TELEGRAM_TOKEN={'LOADED' if TELEGRAM_TOKEN else 'MISSING'}")
logger.info(f"Environment check: OPENAI_API_KEY={'LOADED' if OPENAI_API_KEY else 'MISSING'}")

# Validate tokens
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing! Set it in Render Environment.")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing! Set it in Render Environment.")

# Initialize clients
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

# Telegram Bot Application
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Handlers
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is running! Send me a message.")

async def echo(update: Update, context):
    user_message = update.message.text
    await update.message.reply_text(f"You said: {user_message}")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Webhook Endpoint
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    logger.info("✅ Setting webhook...")
    await application.bot.set_webhook("https://jthang-bot.onrender.com/webhook")
    await application.initialize()
    await application.start()
    logger.info("✅ Webhook set successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
