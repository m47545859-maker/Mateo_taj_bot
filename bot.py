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

from data import ANSWERS, PLAYERS, CLUBS


BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

OWNER = "@Maga_unknown"
OWNER_URL = "https://t.me/Maga_unknown"


UNKNOWN_ANSWER = (
    "Ман ҷавоби саволи шуморо намедонам.\n\n"
    "Шумо метавонед ин саволро аз Owner — @Maga_unknown пурсед."
)


# =========================
# RENDER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Mateo is alive!")

    def log_message(self, format, *args):
        pass


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# =========================
# NORMALIZE
# =========================

def normalize(text):
    text = text.lower().strip()

    replacements = {
        "ё": "е",
        "ӣ": "и",
        "қ": "к",
        "ғ": "г",
        "ҳ": "х",
        "ҷ": "ч",
        "ӯ": "у",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Ҳамаи аломатҳо нест мешаванд
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)

    # Фосилаҳои зиёдатӣ нест мешаванд
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================
# MATEO MUST BE FIRST
# =========================

def get_question(text):

    text = text.strip()

    # Танҳо агар Mateo/Матео дар аввал бошад
    match = re.match(
        r"^(матео|mateo)\b",
        text,
        flags=re.IGNORECASE
    )

    if not match:
        return None

    question = text[match.end():].strip()

    return question


# =========================
# ANSWER FROM DATABASE
# =========================

def find_answer(question):

    q = normalize(question)

    if not q:
        return None

    # Аввал ҷавоби аниқ
    if q in ANSWERS:
        return ANSWERS[q]

    # Баъд муқоисаи normalizeшуда
    for key, answer in ANSWERS.items():

        if normalize(key) == q:
            return answer

    return None


# =========================
# PLAYER
# =========================

def find_player(question):

    q = normalize(question)

    # Номи дарозтар аввал санҷида мешавад
    players = sorted(
        PLAYERS.items(),
        key=lambda x: len(normalize(x[0])),
        reverse=True
    )

    for key, player in players:

        if normalize(key) in q:
            return player

    return None


def player_answer(player, question):

    q = normalize(question)

    name = player["name"]
    club = player["club"]
    league = player["league"]
    country = player["country"]
    position = player["position"]

    if (
        "кадом даста" in q
        or "кадом клуб" in q
        or "дар кучо бозӣ" in q
    ):
        return f"{name} дар {club} бозӣ мекунад. ⚽"

    if "кадом лига" in q:
        return f"{name} дар {league} бозӣ мекунад. 🏆"

    if (
        "миллат" in q
        or "кадом кишвар" in q
        or "аз кадом кишвар" in q
    ):
        return f"{name} аз {country} мебошад. 🌍"

    if (
        "позиция" in q
        or "позитсия" in q
        or "мавкеъ" in q
    ):
        return f"Позицияи {name} — {position}. ⚽"

    return (
        f"👤 Бозигар\n"
        f"→ Ном: {name}\n"
        f"→ Клуб: {club}\n"
        f"→ Лига: {league}\n"
        f"→ Миллат: {country}\n"
        f"→ Позиция: {position}"
    )


# =========================
# CLUB
# =========================

def find_club(question):

    q = normalize(question)

    clubs = sorted(
        CLUBS.items(),
        key=lambda x: len(normalize(x[0])),
        reverse=True
    )

    for key, club in clubs:

        if normalize(key) in q:
            return club

    return None


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
# MESSAGE
# =========================

async def handle_message(update, context):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    # Агар Mateo дар аввал набошад — ҳеҷ ҷавоб намедиҳад
    question = get_question(text)

    if question is None:
        return

    # Танҳо "Матео"
    if not question.strip():
        await update.message.reply_text(
            "Салом! Ман Матео ҳастам. 🤖"
        )
        return

    # 1. Database answers
    answer = find_answer(question)

    if answer:
        await update.message.reply_text(answer)
        return

    # 2. Player
    player = find_player(question)

    if player:
        await update.message.reply_text(
            player_answer(player, question)
        )
        return

    # 3. Club
    club = find_club(question)

    if club:
        await update.message.reply_text(
            club_answer(club)
        )
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
            "BOT_TOKEN ёфт нашуд! "
            "Дар Render Environment Variables BOT_TOKEN гузоред."
        )

    threading.Thread(
        target=run_server,
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
            handle_message
        )
    )

    print("================================")
    print("MATEO STARTED SUCCESSFULLY")
    print("AI: OFF")
    print("DATABASE: ON")
    print("MATEO PREFIX: ON")
    print("================================")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
