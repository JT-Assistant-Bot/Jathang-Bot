import os
import logging
import httpx
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = "https://jthang-bot.onrender.com/webhook"

if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing!")

# FastAPI app
app = FastAPI()

# Telegram Application
application = Application.builder().token(BOT_TOKEN).build()


async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is alive on Render!")


async def chat_with_gpt(update: Update, context):
    user_message = update.message.text

    if not OPENAI_API_KEY:
        await update.message.reply_text("❌ OpenAI API key is missing!")
        return

    try:
        # Call OpenAI API
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",  # Use GPT-4o-mini for efficiency
            "messages": [{"role": "user", "content": user_message}]
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions",
                                         headers=headers, json=payload)
            data = response.json()
            gpt_reply = data["choices"][0]["message"]["content"]

        await update.message.reply_text(gpt_reply)

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        await update.message.reply_text("⚠️ Sorry, something went wrong while contacting OpenAI.")


# Add handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_gpt))


@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.start()
    await application.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook set: {WEBHOOK_URL}")


@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"status": "ok"}


@app.get("/")
async def home():
    return {"status": "Bot is alive"}
