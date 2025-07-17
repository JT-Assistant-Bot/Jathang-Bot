import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler
import asyncio

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is NOT set!")

WEBHOOK_URL = f"https://jthang-bot.onrender.com/webhook"

# Create FastAPI app
app = FastAPI()

# Create Telegram Application
application = Application.builder().token(BOT_TOKEN).build()

# Define bot command
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is alive on Render using ASGI!")

application.add_handler(CommandHandler("start", start))

@app.on_event("startup")
async def on_startup():
    await application.bot.delete_webhook()
    await application.bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(application.start())
    logger.info(f"✅ Webhook set to: {WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"❌ Error in webhook: {e}")
        return {"status": "error"}
