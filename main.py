import os
import logging
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from openai import AsyncOpenAI

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing!")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing!")

# OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# FastAPI app
app = FastAPI()

# Telegram Application
application = Application.builder().token(TELEGRAM_TOKEN).build()


# ✅ Start Command
async def start(update: Update, context):
    await update.message.reply_text(
        "✅ *Bot is alive on Render!*\n\n"
        "_Send me any message and I'll reply using AI._",
        parse_mode=ParseMode.MARKDOWN
    )


# ✅ Handle all text messages
async def handle_message(update: Update, context):
    user_text = update.message.text
    user_id = update.effective_user.id

    logger.info(f"Message from {user_id}: {user_text}")

    # Generate AI response
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that responds concisely with Markdown formatting."},
                {"role": "user", "content": user_text}
            ]
        )

        ai_reply = response.choices[0].message.content.strip()

        await update.message.reply_text(
            ai_reply,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        await update.message.reply_text("⚠️ Sorry, something went wrong with AI response.")


# ✅ Add Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ✅ FastAPI route for Telegram webhook
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return JSONResponse(content={"ok": True})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse(content={"ok": False}, status_code=500)


# ✅ Root route
@app.get("/")
async def root():
    return {"status": "Bot is running!"}


# ✅ Startup event
@app.on_event("startup")
async def startup():
    url = "https://jthang-bot.onrender.com/webhook"
    await application.bot.set_webhook(url)
    logger.info(f"✅ Webhook set: {url}")
    asyncio.create_task(application.initialize())
    asyncio.create_task(application.start())
