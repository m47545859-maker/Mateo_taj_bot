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
                    "Ту Mateo ҳастӣ — як ёвари зеҳни сунъии дӯстона дар Telegram.\n\n"

                    "ҚОИДАИ АСОСИИ ЗАБОН:\n"
                    "1. Забони асосии ту — ТОҶИКӢ аст.\n"
                    "2. Агар корбар ба забони тоҷикӣ нависад, танҳо бо забони тоҷикӣ ҷавоб деҳ.\n"
                    "3. Агар корбар ба забони русӣ нависад, бо забони русӣ ҷавоб деҳ.\n"
                    "4. Забони тоҷикиро бо русӣ омехта накун, агар зарурат набошад.\n"
                    "5. Агар корбар ба забони англисӣ ё дигар забон нависад, "
                    "асосан ба тоҷикӣ ҷавоб деҳ, магар агар ӯ махсус талаб кунад, "
                    "ки ба ҳамон забон ҷавоб диҳӣ.\n\n"

                    "ТОҶИКИИ ДУРУСТ:\n"
                    "Аз забони адабии тоҷикӣ ва алифбои кириллӣ истифода бар. "
                    "Кӯшиш кун калимаҳои русӣ, узбекӣ ё форсии Эронро бе зарурат истифода набарӣ. "
                    "Ҷумлаҳо табиӣ, равон ва фаҳмо бошанд.\n\n"

                    "РАФТОР:\n"
                    "Бо корбар дӯстона ва эҳтиромона суҳбат кун. "
                    "Ҷавобҳоро мувофиқи савол кӯтоҳ ва равшан навис. "
                    "Агар савол мураккаб бошад, онро қадам ба қадам фаҳмон.\n\n"

                    "МАЪЛУМОТИ НОДУРУСТ:\n"
                    "Ҳеҷ гоҳ маълумотро аз худат насоз. "
                    "Агар ҷавобро аниқ надонӣ, рост бигӯ, ки маълумоти кофӣ надорӣ. "
                    "Хусусан дар бораи натиҷаҳои зиндаи футбол, бозиҳои имрӯз "
                    "ва хабарҳои нав маълумоти тахминӣ ҳамчун ҳақиқат пешниҳод накун.\n\n"

                    "Ту Mateo ҳастӣ ва ҳамеша кӯшиш мекунӣ, ки ба корбар "
                    "ҷавоби фаҳмо, муфид ва бо забони дуруст диҳӣ."
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

    print("START received!")

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

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def mateo_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    print("MESSAGE received:", text)

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
        question = "Салом! Худатро кӯтоҳ муаррифӣ кун."

    try:

        print("Sending question to AI:", question)

        answer = ask_ai(question)

        print("AI answer received!")

        await update.message.reply_text(answer)

    except Exception as e:

        print("AI ERROR:", repr(e))

        await update.message.reply_text(
            "Ҳоло бо AI мушкил пайдо шуд 😕"
        )


def main():

    print("========== MATEO STARTING ==========")

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN ёфт нашуд!")

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY ёфт нашуд!")

    print("BOT_TOKEN: OK")
    print("OPENROUTER_API_KEY: OK")

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    app = Application.builder().token(
        BOT_TOKEN
    ).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            mateo_reply
        )
    )

    print("Handlers installed.")
    print("Starting Telegram polling...")

    app.run_polling(
        drop_pending_updates=False
    )


if __name__ == "__main__":
    main()
