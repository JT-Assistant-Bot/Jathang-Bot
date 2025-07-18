import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import AsyncOpenAI

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing!")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing!")

# ✅ Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ✅ Allowed user (private bot)
ALLOWED_USER_ID = 5927345569  # Your Telegram ID

# ✅ FastAPI app
app = FastAPI()

# ✅ Telegram app
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()


# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hello! Your private assistant is ready. Ask me anything!")


# ✅ Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ Access denied. This bot is private.")
        return

    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": text}
            ]
        )
        answer = completion.choices[0].message["content"]
        await update.message.reply_text(answer)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Something went wrong.")


# ✅ Register handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ✅ Webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    webhook_url = "https://jthang-bot.onrender.com/webhook"
    await telegram_app.bot.set_webhook(webhook_url)
    logger.info(f"✅ Webhook set successfully at {webhook_url}")
