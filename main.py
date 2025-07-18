import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext import ContextTypes
from openai import AsyncOpenAI

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = 5927345569  # Your Telegram user ID

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing!")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing!")

# OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# FastAPI app
app = FastAPI()

# Telegram app
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    await update.message.reply_text("✅ Hello JT! Your private AI assistant is ready.")

# ✅ Chat handler for OWNER only
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return

    user_message = update.message.text
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are JT's personal AI assistant. Respond concisely."},
                {"role": "user", "content": user_message}
            ]
        )
        ai_reply = response.choices[0].message.content
        await update.message.reply_text(ai_reply)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ✅ Add handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

# ✅ Webhook route
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    webhook_url = "https://jthang-bot.onrender.com/webhook"
    await telegram_app.bot.set_webhook(url=webhook_url)
    logger.info(f"✅ Webhook set successfully at {webhook_url}")
