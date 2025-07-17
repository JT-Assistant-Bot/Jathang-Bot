import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is missing!")

# Initialize FastAPI app
app = FastAPI()

# Initialize Telegram bot Application
application = Application.builder().token(BOT_TOKEN).build()

# Define a simple /start command
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is alive and working via Render!")

# Add handler
application.add_handler(CommandHandler("start", start))

# Start the bot in background
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(application.initialize())
    asyncio.create_task(application.start())
    asyncio.create_task(application.updater.start_polling())  # Not required for webhook but good for fallback

# Stop the bot when app shuts down
@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
    await application.shutdown()

# Webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
    return {"status": "ok"}

# Root route
@app.get("/")
async def root():
    return {"message": "✅ Bot is running on Render!"}
