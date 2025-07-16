import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Get environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "5927345569"))  # Default to your ID

openai.api_key = OPENAI_API_KEY

# ✅ Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != BOT_OWNER_ID:
        await update.message.reply_text("❌ Access Denied!")
        return
    await update.message.reply_text("✅ Hi JT! Your personal assistant is online and ready.")

# ✅ Handle normal messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != BOT_OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    user_text = update.message.text

    try:
        # Send message to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Lightweight and fast
            messages=[
                {"role": "system", "content": "You are JT's personal assistant. Respond concisely and helpfully."},
                {"role": "user", "content": user_text}
            ]
        )

        bot_reply = response["choices"][0]["message"]["content"].strip()
        await update.message.reply_text(bot_reply)

    except Exception as e:
        await update.message.reply_text(f"⚠ Error: {e}")

# ✅ Main function
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
