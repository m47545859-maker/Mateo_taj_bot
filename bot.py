import os
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

async def mateo_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # Фақат вақте ҷавоб медиҳад, ки "Матео" ё "Mateo" навишта шавад
    if re.search(r"\b(?:mateo|матео)\b", text, re.IGNORECASE):
        await update.message.reply_text(
            "Салом! 👋 Ман Mateo ҳастам. Чӣ кӯмак кунам?"
        )

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN ёфт нашуд!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            mateo_reply
        )
    )

    print("Mateo фаъол шуд...")
    app.run_polling()

if __name__ == "__main__":
    main()
