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


# =========================================================
# RENDER WEB SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Mateo is alive!")

    def log_message(self, format, *args):
        pass


def run_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


# =========================================================
# NORMALIZE TEXT
# =========================================================

def normalize(text):

    text = text.lower().strip()

    # Tajik / Cyrillic normalization
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

    # Remove punctuation
    text = re.sub(
        r"""[!?.,:;'"«»(){}<>/\-–—_+=*#@]+""",
        " ",
        text
    )

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# MATEO PREFIX
# =========================================================

def remove_mateo_prefix(text):

    text = text.strip()

    # Mateo must be at the VERY BEGINNING
    pattern = r"^(матео|mateo)\b"

    match = re.match(
        pattern,
        text,
        flags=re.IGNORECASE
    )

    if not match:
        return None

    question = text[match.end():].strip()

    # Remove punctuation after Mateo
    question = re.sub(
        r"^[!?.,:;«»(){}\-–—]+",
        "",
        question
    )

    return question.strip()


# =========================================================
# FIND NORMAL ANSWER
# =========================================================

def find_answer(question):

    q = normalize(question)

    if not q:
        return None

    # Exact match
    if q in ANSWERS:
        return ANSWERS[q]

    # Compare normalized keys
    for key, answer in ANSWERS.items():

        normalized_key = normalize(key)

        if q == normalized_key:
            return answer

    return None


# =========================================================
# FIND PLAYER
# =========================================================

def find_player(question):

    q = normalize(question)

    if not q:
        return None

    # Longest names first
    sorted_players = sorted(
        PLAYERS.items(),
        key=lambda item: len(normalize(item[0])),
        reverse=True
    )

    for key, player in sorted_players:

        player_key = normalize(key)

        if player_key in q:
            return player

    return None


# =========================================================
# PLAYER ANSWER
# =========================================================

def player_answer(player, question):

    q = normalize(question)

    name = player["name"]
    club = player["club"]
    league = player["league"]
    country = player["country"]
    position = player["position"]

    # Club
    if (
        "кадом даста" in q
        or "кадом клуб" in q
        or "дар кучо бозӣ" in q
        or "дар кучо бозии" in q
    ):
        return (
            f"{name} дар клуби {club} бозӣ мекунад. ⚽"
        )

    # League
    if "кадом лига" in q:
        return (
            f"{name} дар {league} бозӣ мекунад. 🏆"
        )

    # Country
    if (
        "аз кадом кишвар" in q
        or "кадом кишвар" in q
        or "аз кучо" in q
        or "миллат" in q
    ):
        return (
            f"{name} аз {country} мебошад. 🌍"
        )

    # Position
    if (
        "позиция" in q
        or "позитсия" in q
        or "дар кадом мавкеъ" in q
    ):
        return (
            f"Позицияи {name} — {position}. ⚽"
        )

    # Full player information
    return (
        f"👤 {name}\n\n"
        f"🏟 Клуб: {club}\n"
        f"🏆 Лига: {league}\n"
        f"🌍 Миллат: {country}\n"
        f"⚽ Позиция: {position}"
    )


# =========================================================
# FIND CLUB
# =========================================================

def find_club(question):

    q = normalize(question)

    if not q:
        return None

    sorted_clubs = sorted(
        CLUBS.items(),
        key=lambda item: len(normalize(item[0])),
        reverse=True
    )

    for key, club in sorted_clubs:

        club_key = normalize(key)

        if club_key in q:
            return club

    return None


# =========================================================
# CLUB ANSWER
# =========================================================

def club_answer(club):

    return (
        f"🏟 {club['name']}\n\n"
        f"🏆 Лига: {club['league']}\n"
        f"🌍 Кишвар: {club['country']}"
    )


# =========================================================
# START
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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


# =========================================================
# MATEO MESSAGE
# =========================================================

async def mateo_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    # Mateo MUST be at the beginning
    question = remove_mateo_prefix(text)
