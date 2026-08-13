import os
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import ANSWERS
from players import PLAYERS
from clubs import CLUBS


BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

OWNER_USERNAME = "Maga_unknown"
OWNER_URL = "https://t.me/Maga_unknown"

UNKNOWN_ANSWER = (
    "Ман ҷавоби саволи шуморо намедонам. "
    "Шумо метавонед ин саволро аз Owner — @Maga_unknown пурсед."
)


# =========================
# RENDER HEALTH CHECK
# =========================

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


# =========================
# TEXT NORMALIZATION
# =========================

def normalize(text):
    text = text.lower().strip()

    text = text.replace("ё", "е")
    text = text.replace("ӣ", "и")
    text = text.replace("қ", "к")
    text = text.replace("ғ", "г")
    text = text.replace("ҳ", "х")
    text = text.replace("ҷ", "ч")
    text = text.replace("ӯ", "у")

    text = re.sub(r"[!?.,:;\"'«»()\-–—]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================
# CHECK MATEO PREFIX
# =========================

def remove_mateo_prefix(text):

    original = text.strip()

    pattern = r"^(матео|mateo)(?:\s*[,!:.\-]?\s*)(.*)$"

    match = re.match(
        pattern,
        original,
        flags=re.IGNORECASE
    )

    if not match:
        return None

    question = match.group(2).strip()

    return question


# =========================
# FIND NORMAL ANSWER
# =========================

def find_answer(question):

    q = normalize(question)

    if q in ANSWERS:
        return ANSWERS[q]

    # partial matching
    for key, answer in ANSWERS.items():

        normalized_key = normalize(key)

        if q == normalized_key:
            return answer

    return None


# =========================
# FIND PLAYER
# =========================

def find_player(question):

    q = normalize(question)

    for key, player in PLAYERS.items():

        key_normalized = normalize(key)

        if key_normalized in q:

            return player

    return None


# =========================
# FIND CLUB
# =========================

def find_club(question):

    q = normalize(question)

    for key, club in CLUBS.items():

        key_normalized = normalize(key)

        if key_normalized in q:

            return club

    return None


# =========================
# PLAYER ANSWER
# =========================

def player_answer(player, question):

    q = normalize(question)

    name = player["name"]
    club = player["club"]
    league = player["league"]
    country = player["country"]
    position = player["position"]

    if "кадом даста" in q or "кадом клуб" in q:
        return f"{name} дар клуби {club} бозӣ мекунад. ⚽"

    if "кадом лига" in q:
        return f"{name} дар {league} бозӣ мекунад. ⚽"

    if "кадом кишвар" in q or "аз кадом кишвар" in q:
        return f"{name} аз {country} мебошад. 🌍"

    if "позиция" in q or "позитсия" in q:
        return f"Позицияи {name} — {position}. ⚽"

    return (
        f"👤 {name}\n\n"
        f"🏟 Клуб: {club}\n"
        f"🏆 Лига: {league}\n"
        f"🌍 Миллат: {country}\n"
        f"⚽ Позиция: {position}"
    )


# =========================
# CLUB ANSWER
# =========================

def club_answer(club):

    return (
        f"🏟 {club['name']}\n\n"
        f"🏆 Лига: {club['league']}\n"
        f"🌍 Кишвар: {club['country']}"
    )


# =========================
# /START
# =========================

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

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# MATEO MESSAGE
# =========================

async def mateo_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    # IMPORTANT:
    # If message does NOT start with Mateo/Mateo -> SILENCE

    question = remove_mateo_prefix(text)

    if question is None:
        return

    if not question:
        await update.message.reply_text(
            "Бале? 🤖 Саволатонро нависед."
        )
        return

    # 1. Normal predefined answers
    answer = find_answer(question)

    if answer:
        await update.message.reply_text(answer)
        return

    # 2. Player database
    player = find_player(question)

    if player:
        answer = player_answer(player, question)
        await update.message.reply_text(answer)
        return

    # 3. Club database
    club = find_club(question)

    if club:
        answer = club_answer(club)
        await update.message.reply_text(answer)
        return

    # 4. Unknown
    await update.message.reply_text(
        UNKNOWN_ANSWER
    )


# =========================
# MAIN
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN ёфт нашуд!"
        )

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            mateo_message
        )
    )

    print("Mateo is starting...")
    print("AI: OFF")
    print("Database: ON")
    print("Mateo prefix required: ON")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
