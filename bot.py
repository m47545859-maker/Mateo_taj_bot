import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Mateo is alive!")

    def log_message(self, format, *args):
        return


def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


async def mateo_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text

    if re.search(r"(^|\\s)(mateo|матео)(\\s|$|[,!?])", text, re.IGNORECASE):
        await update.message.reply_text(
            "Салом! 👋 Ман Mateo ҳастам. Чӣ кӯмак кунам?"
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN ёфт нашуд!")

    threading.Thread(target=run_web_server, daemon=True).start()

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
