import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

PORT = int(os.getenv("PORT", "10000"))

MODEL = "openrouter/free"

OWNER_USERNAME = "Maga_unknown"
OWNER_URL = "https://t.me/Maga_unknown"


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Mateo AI is alive!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


def ask_ai(question):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ту Mateo ҳастӣ, як боти дӯстона дар Telegram. "
                    "Асосан бо забони тоҷикӣ ҷавоб деҳ. "
                    "Агар корбар русӣ нависад, ба русӣ ҷавоб деҳ. "
                    "Ҷавобҳоро кӯтоҳ, табиӣ ва фаҳмо нигоҳ дор."
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    return result["choices"][0]["message"]["content"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🤖 Салом! Ман Mateo ҳастам.\n\n"
        "Ман як ёвари зеҳни сунъӣ ҳастам, ки барои "
        "муошират ва кӯмак ба корбарон сохта шудаам.\n\n"
        "💬 Ман метавонам ба саволҳо ҷавоб диҳам, "
        "бо ту суҳбат кунам, матн нависам, тарҷума кунам "
        "ва ба бисёр масъалаҳо кӯмак расонам.\n\n"
        "👥 Дар гурӯҳҳо маро бо навиштани "
        "«Матео» фаъол карда метавонед.\n\n"
        "👤 Owner: @Maga_unknown\n"
        "🛠️ Created by: @Maga_unknown"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "👤 Owner — @Maga_unknown",
                url=OWNER_URL
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text,
        reply_markup=reply_markup
    )


async def mateo_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    match = re.search(
        r"(^|\s)(mateo|матео)(\s|$|[,!?])",
        text,
        re.IGNORECASE,
    )

    if not match:
        return

    question = re.sub(
        r"(^|\s)(mateo|матео)(\s*[,!?]?\s*)",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    ).strip()

    if not question:
        question = (
            "Салом! Худатро кӯтоҳ муаррифӣ кун."
        )

    try:

        answer = ask_ai(question)

        await update.message.reply_text(answer)

    except Exception as e:

        print("AI ERROR:", e)

        await update.message.reply_text(
            "Ҳоло бо AI мушкил пайдо шуд 😕"
        )


def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN ёфт нашуд!"
        )

    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY ёфт нашуд!"
        )

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    # /start
    app.add_handler(
        CommandHandler("start", start)
    )

    # Mateo / Матео
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            mateo_reply
        )
    )

    print("Mateo AI фаъол шуд!")

    app.run_polling()


if __name__ == "__main__":
    main()
