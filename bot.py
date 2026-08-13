import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.getenv("PORT", "10000"))

MODEL = "openrouter/free"


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Mateo is alive!")

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
                    "Ба корбарон асосан бо забони тоҷикӣ ҷавоб деҳ. "
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


async def mateo_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
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
        question = "Салом! Бо ман шинос шав ва худро кӯтоҳ муаррифӣ кун."

    try:
        answer = ask_ai(question)
        await update.message.reply_text(answer)

    except Exception as e:
        print("AI ERROR:", e)
        await update.message.reply_text(
            "Ҳоло бо AI мушкил пайдо шуд 😕 Баъдтар боз кӯшиш кун."
        )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN ёфт нашуд!")

    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY ёфт нашуд!")

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            mateo_reply
        )
    )

    print("Mateo AI фаъол шуд...")

    app.run_polling()


if __name__ == "__main__":
    main()
