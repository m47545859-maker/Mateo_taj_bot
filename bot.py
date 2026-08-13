import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

PORT = int(os.getenv("PORT", "10000"))

OWNER = "@Maga_unknown"
OWNER_URL = "https://t.me/Maga_unknown"

# Free-tier compatible Flash model
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


# =========================================================
# GEMINI
# =========================================================

if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )
else:
    gemini_client = None


SYSTEM_PROMPT = """
Ту Mateo ҳастӣ — боти дӯстона ва табиии тоҷикзабон.

ҚОИДАҲО:

1. Забони асосии ту тоҷикӣ аст.
2. Агар корбар ба русӣ нависад, ба русӣ ҷавоб деҳ.
3. Ба дигар забонҳо ҷавоб надеҳ.
4. Агар матн ба забони ғайр аз тоҷикӣ ё русӣ бошад, бигӯ:
   "Ман танҳо забони тоҷикӣ ва русиро мефаҳмам."

5. Бо корбар озодона суҳбат кун.
6. Ҷавобҳо бояд табиӣ ва дӯстона бошанд.
7. Агар корбар салом кунад, салом кун.
8. Агар шӯхӣ кунад, муносиб ҷавоб деҳ.
9. Агар саволро надонӣ, маълумоти сохта насоз.
10. Номи ту Mateo аст.
11. Owner-и ту @Maga_unknown мебошад.
12. Нагӯ, ки ту ChatGPT ҳастӣ.

ФУТБОЛ:

Ту дар бораи футбол, клубҳо, бозигарон ва мураббиён
метавонӣ суҳбат кунӣ.

Дастаи дӯстдоштаи ту:
Манчестер Сити.

Агар пурсанд:
"Мухлиси кадом дастаӣ?"
ҷавоб деҳ:
"Ман мухлиси дастаи шоҳона, яъне Манчестер Сити ҳастам. 💙⚽"

Ҷавобҳо асосан тоҷикӣ бошанд.
"""


# =========================================================
# MEMORY
# =========================================================

memory = {}

MAX_MESSAGES = 12


def get_memory(user_id):

    if user_id not in memory:
        memory[user_id] = []

    return memory[user_id]


def save_message(user_id, role, text):

    history = get_memory(user_id)

    history.append({
        "role": role,
        "text": text
    })

    if len(history) > MAX_MESSAGES:
        memory[user_id] = history[-MAX_MESSAGES:]


# =========================================================
# MATEO NAME CHECK
# =========================================================

def has_mateo(text):

    text = text.lower()

    return (
        "матео" in text
        or "mateo" in text
    )


def remove_mateo(text):

    text = text.replace(
        "Матео",
        ""
    )

    text = text.replace(
        "матео",
        ""
    )

    text = text.replace(
        "МАТЕО",
        ""
    )

    text = text.replace(
        "Mateo",
        ""
    )

    text = text.replace(
        "mateo",
        ""
    )

    text = text.replace(
        "MATEO",
        ""
    )

    return " ".join(
        text.split()
    ).strip()


# =========================================================
# SPECIAL ANSWERS
# =========================================================

def special_answer(question):

    q = question.lower()

    # Removes punctuation mentally
    q = (
        q.replace("?", "")
         .replace("!", "")
         .replace(",", "")
         .replace(".", "")
         .replace(":", "")
    )

    q = " ".join(q.split())

    fan_phrases = [
        "мухлиси кадом дастаи",
        "мухлиси кадом дастаи хасти",
        "ту мухлиси кадом дастаи",
        "ту мухлиси кадом дастаи хасти",
        "дастаи дустдоштаи ту",
        "кадом даста ба ту маъкул аст",
    ]

    for phrase in fan_phrases:

        if phrase in q:

            return (
                "Ман мухлиси дастаи шоҳона, "
                "яъне Манчестер Сити ҳастам. 💙⚽"
            )

    return None


# =========================================================
# LANGUAGE CHECK
# =========================================================

def is_cyrillic(text):

    for char in text:

        if (
            "А" <= char <= "я"
            or char in "ЁёӢӣҚқҒғҲҳҶҷӮӯ"
        ):
            return True

    return False


def contains_latin(text):

    return any(
        "a" <= char.lower() <= "z"
        for char in text
    )


# =========================================================
# GEMINI CHAT
# =========================================================

def ask_gemini(user_id, question):

    if not gemini_client:

        return (
            "Gemini API фаъол нест.\n\n"
            "Дар Render → Environment "
            "GEMINI_API_KEY-ро гузоред."
        )

    history = get_memory(user_id)

    conversation = SYSTEM_PROMPT + "\n\n"

    for item in history:

        if item["role"] == "user":

            conversation += (
                "Корбар: "
                + item["text"]
                + "\n"
            )

        else:

            conversation += (
                "Mateo: "
                + item["text"]
                + "\n"
            )

    conversation += (
        "Корбар: "
        + question
        + "\n"
        "Mateo:"
    )

    try:

        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=conversation
        )

        answer = response.text.strip()

        save_message(
            user_id,
            "user",
            question
        )

        save_message(
            user_id,
            "assistant",
            answer
        )

        return answer

    except Exception as error:

        print(
            "GEMINI ERROR:",
            repr(error)
        )

        return (
            "Ҳоло Mateo ба AI пайваст шуда натавонист. "
            "Каме баъдтар кӯшиш кунед."
        )


# =========================================================
# RENDER WEB SERVER
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/plain; charset=utf-8"
        )

        self.end_headers()

        self.wfile.write(
            "Mateo is alive! 🤖".encode("utf-8")
        )

    def log_message(self, format, *args):
        pass


def run_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        "Render web server started"
    )

    server.serve_forever()


# =========================================================
# START COMMAND
# =========================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "🤖 Салом! Ман Mateo ҳастам.\n\n"
        "Ман як ёвари тоҷикзабон ҳастам, ки "
        "метавонам бо шумо озодона суҳбат кунам "
        "ва ба саволҳои шумо ҷавоб диҳам.\n\n"
        "💬 Дар суҳбат маро бо номи "
        "«Матео» ё «Mateo» даъват кунед.\n\n"
        "⚽ Ман инчунин метавонам дар бораи "
        "футбол, бозигарон, клубҳо ва дигар "
        "мавзӯъҳо суҳбат кунам.\n\n"
        "🇹🇯 Забони асосӣ: тоҷикӣ\n"
        "🇷🇺 Русӣ низ дастгирӣ мешавад.\n\n"
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
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# MESSAGE
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    text = update.message.text

    if not text:
        return

    # Mateo MUST be somewhere in message
    if not has_mateo(text):

        return

    question = remove_mateo(text)

    # Just "Mateo"
    if not question:

        await update.message.reply_text(
            "Салом! Ман Матео ҳастам. 🤖"
        )

        return

    # Special fixed answers
    special = special_answer(
        question
    )

    if special:

        await update.message.reply_text(
            special
        )

        return

    # AI
    user_id = update.effective_user.id

    answer = ask_gemini(
        user_id,
        question
    )

    await update.message.reply_text(
        answer
    )


# =========================================================
# MAIN
# =========================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN ёфт нашуд!"
        )

    if not GEMINI_API_KEY:

        print(
            "WARNING: GEMINI_API_KEY ёфт нашуд!"
        )

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    print(
        "===================================="
    )

    print(
        "MATEO STARTED SUCCESSFULLY 🤖"
    )

    print(
        "GEMINI AI: ON"
    )

    print(
        "TAJIK: ON"
    )

    print(
        "RUSSIAN: ON"
    )

    print(
        "MATEO ANYWHERE IN MESSAGE: ON"
    )

    print(
        "===================================="
    )

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
