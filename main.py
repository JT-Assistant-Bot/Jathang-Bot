import os
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from gtts import gTTS
from openai import OpenAI

# ✅ Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am your assistant. How can I help you today?")

# ✅ /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can ask me anything or give a command!")

# ✅ Handle text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = get_ai_response(user_message)

    # Send text response
    await update.message.reply_text(response)

    # Send voice response
    audio_file = text_to_voice(response)
    with open(audio_file, 'rb') as audio:
        await update.message.reply_voice(voice=audio)

# ✅ AI response using OpenAI GPT
def get_ai_response(user_message: str) -> str:
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Be brief and precise."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# ✅ Convert text to speech using gTTS
def text_to_voice(text):
    tts = gTTS(text=text, lang='en')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

# ✅ Main entry point
def main():
    if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
        print("❌ ERROR: TELEGRAM_TOKEN or OPENAI_API_KEY not set in environment variables!")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # ✅ Add command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
