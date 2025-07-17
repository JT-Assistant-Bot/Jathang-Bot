import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set!")

WEBHOOK_URL = f"https://jthang-bot.onrender.com/webhook"

# Telegram App
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is alive on Render!")

application.add_handler(CommandHandler("start", start))

# Start Bot
async def start_bot():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook set: {WEBHOOK_URL}")

# FastAPI App
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_bot())

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error in webhook: {e}")
    return {"ok": True}

@app.get("/")
async def home():
    return {"status": "Bot running on Render!"}
