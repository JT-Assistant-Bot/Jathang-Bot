import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import uvicorn
from openai import AsyncOpenAI

# ✅ Enable Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Load Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN is missing!")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY is missing!")

# ✅ Initialize OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# ✅ FastAPI App
app = FastAPI()

# ✅ Initialize Telegram App
application = Application.builder().token(TELEGRAM_TOKEN).build()

# ✅ /start command handler
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot is alive on Render and ready to chat!")

# ✅ OpenAI Response Handler
async def chat_with_openai(prompt: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap model
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI Error: {e}")
        return "⚠️ Sorry, I couldn't process your request right now."

# ✅ Handle all text messages
async def handle_message(update: Update, context):
    user_message = update.message.text
    logger.info(f"User: {user_message}")
    reply = await chat_with_openai(user_message)
    await update.message.reply_text(reply)

# ✅ Add Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ✅ Webhook Endpoint
@app.post("/webhook")
async def webhook(request: Request):
    try:
        update = Update.de_json(await request.json(), application.bot)
        await application.process_update(update)
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.get("/")
async def home():
    return {"message": "Bot is running on Render!"}

# ✅ Startup Event: Set Webhook
@app.on_event("startup")
async def set_webhook():
    url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    await application.bot.set_webhook(url)
    logger.info(f"✅ Webhook set: {url}")

# ✅ Run Uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
