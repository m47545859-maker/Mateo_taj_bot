import os
import re
import json
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


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")

PORT = int(os.getenv("PORT", "10000"))

OWNER = "@Maga_unknown"
OWNER_URL = "https://t.me/Maga_unknown"

# OpenAI-compatible API
AI_URL = "https://api.openai.com/v1/chat/completions"

# Модели метавонанд иваз шаванд.
AI_MODEL = os.getenv("AI_MODEL", "gpt-5-mini")


# =========================================================
# MATEO PERSONALITY
# =========================================================

SYSTEM_PROMPT = """
Ту Mateo ҳастӣ.

Ту як ёвари дӯстона, хушмуомила ва табиии тоҷикзабон ҳастӣ.

ҚОИДАҲО:

1. Забони асосии ту ТОҶИКӢ аст.
2. Агар корбар ба русӣ нависад, ба русӣ ҷавоб деҳ.
3. Ба забонҳои дигар ҷавоб надеҳ.
4. Агар корбар ба забони ғайр аз тоҷикӣ ё русӣ нависад, кӯтоҳ бигӯ:
   "Ман танҳо забони тоҷикӣ ва русиро мефаҳмам."

5. Бо корбар озодона суҳбат кун.
6. Ҷавобҳо бояд табиӣ бошанд, мисли суҳбати одии инсон.
7. Ҳар саволро танҳо бо ҷавоби кӯтоҳи якхела маҳдуд накун.
8. Агар корбар шӯхӣ кунад, муносиб ҷавоб деҳ.
9. Агар корбар салом кунад, салом кун.
10. Агар корбар дар бораи футбол пурсад, ба мавзӯи футбол муносиб ҷавоб деҳ.
11. Агар маълумоти дақиқро надонӣ, рост бигӯ, ки намедонӣ.
12. Ҳеҷ гоҳ нагӯ, ки ту ChatGPT ҳастӣ.
13. Номи ту Mateo аст.
14. Owner-и ту @Maga_unknown мебошад.
15. Ту бояд худро ҳамчун Mateo муаррифӣ кун.

ФУТБОЛ:

Агар корбар дар бораи Манчестер Сити пурсад:
- ту мухлиси Манчестер Сити ҳастӣ.
- Метавонӣ дар бораи футбол, клубҳо, бозигарон ва мураббиён суҳбат кунӣ.

Агар маълумоти футболӣ талаб карда шавад ва ту итминон надошта бошӣ,
маълумоти сохта надиҳ.

Ҷавобҳо табиӣ, дӯстона ва асосан ба забони тоҷикӣ бошанд.
"""


# =========================================================
# MEMORY
# =========================================================

user_memory = {}

MAX_MEMORY_MESSAGES = 12


def get_memory(user_id):

    if user_id not in user_memory:
        user_memory[user_id] = []

    return user_memory[user_id]


def add_memory(user_id, role, content):

    memory = get_memory(user_id)

    memory.append({
        "role": role,
        "content": content
    })

    if len(memory) > MAX_MEMORY_MESSAGES:
        del memory[:-MAX_MEMORY_MESSAGES]


# =========================================================
# LANGUAGE CHECK
# =========================================================

def contains_cyrillic(text):

    return bool(
        re.search(
            r"[А-Яа-яЁёА-Яа-яӢӣҚқҒғҲҳҶҷӮӯ]",
            text
        )
    )


def looks_english(text):

    english_words = [
        "the",
        "what",
        "who",
        "how",
        "why",
        "where",
        "when",
        "hello",
        "hi",
        "please",
        "thanks",
        "football",
        "city",
        "player",
        "team",
        "you",
        "are",
        "is",
        "can",
        "do",
    ]

    words = re.findall(
        r"[A-Za-z]+",
        text.lower()
    )

    if not words:
        return False

    matches = sum(
        1 for word in words
        if word in english_words
    )

    return matches >= 1


# =========================================================
# FIND MATEO
# =========================================================

def has_mateo(text):

    normalized = text.lower()

    normalized = normalized.replace(
        "ё",
        "е"
    )

    # Mateo / Матео дар ҳар ҷои паём
    patterns = [
        r"\bматео\b",
        r"\bmateo\b",
    ]

    for pattern in patterns:

        if re.search(
            pattern,
            normalized,
            flags=re.IGNORECASE
        ):
            return True

    return False


def remove_mateo(text):

    text = re.sub(
        r"\bматео\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\bmateo\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# SPECIAL MATEO ANSWERS
# =========================================================

def special_answer(question):

    q = question.lower()

    # punctuation
    q = re.sub(
        r"[?!.,:;]+",
        " ",
        q
    )

    q = re.sub(
        r"\s+",
        " ",
        q
    ).strip()

    # FAN
    fan_questions = [
        "мухлиси кадом дастаи",
        "мухлиси кадом дастаи хасти",
        "ту мухлиси кадом дастаи",
        "ту мухлиси кадом дастаи хасти",
        "кадом даста ба ту маъкул аст",
        "дастаи дустдоштаи ту кадом аст",
    ]

    for item in fan_questions:

        if item in q:

            return (
                "Ман мухлиси дастаи шоҳона, "
                "яъне Манчестер Сити ҳастам. 💙⚽"
            )

    return None


# =========================================================
# AI REQUEST
# =========================================================

def ask_ai(user_id, question):

    if not AI_API_KEY:
        return (
            "AI API фаъол нест. "
            "Owner бояд AI_API_KEY-ро дар Render гузорад."
        )

    memory = get_memory(user_id)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(memory)

    messages.append({
        "role": "user",
        "content": question
    })

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 600
    }

    try:

        response = requests.post(
            AI_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:

            print(
                "AI ERROR:",
                response.status_code,
                response.text
            )

            return (
                "Ҳоло дар пайвастшавӣ ба AI мушкил пайдо шуд. "
                "Каме баъдтар кӯшиш кунед."
            )

        data = response.json()

        answer = (
            data["choices"][0]["message"]["content"]
            .strip()
        )

        add_memory(
            user_id,
            "user",
            question
        )

        add_memory(
            user_id,
            "assistant",
            answer
        )

        return answer

    except Exception as e:

        print(
            "AI EXCEPTION:",
            repr(e)
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
            "Mateo is alive! 🤖".encode(
                "utf-8"
            )
        )

    def log_message(
        self,
        format,
        *args
    ):
        pass


def run_web_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        f"Web server started on port {PORT}"
    )

    server.serve_forever()


# =========================================================
# START
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
        "⚽ Ман инчунин ба мавзӯъҳои футбол, "
        "бозигарон, клубҳо ва дигар масъалаҳо "
        "суҳбат карда метавонам.\n\n"
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
# MESSAGE HANDLER
# =========================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    # =====================================================
    # IMPORTANT:
    # Mateo must be anywhere in the message.
    # If no Mateo -> absolutely no response.
    # =====================================================

    if not has_mateo(text):
        return

    question = remove_mateo(text)

    if not question:

        await update.message.reply_text(
            "Салом! Ман Матео ҳастам. 🤖"
        )

        return

    # =====================================================
    # LANGUAGE
    # =====================================================

    # Агар матн лотинӣ бошад ва ба англисӣ монанд бошад
    if looks_english(question) and not contains_cyrillic(question):

        await update.message.reply_text(
            "Ман танҳо забони тоҷикӣ ва русиро мефаҳмам. 🇹🇯🇷🇺"
        )

        return

    # =====================================================
    # SPECIAL ANSWERS
    # =====================================================

    special = special_answer(question)

    if special:

        await update.message.reply_text(
            special
        )

        return

    # =====================================================
    # AI
    # =====================================================

    user_id = update.effective_user.id

    answer = ask_ai(
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
            "BOT_TOKEN ёфт нашуд! "
            "Дар Render → Environment → "
            "BOT_TOKEN гузоред."
        )

    if not AI_API_KEY:

        print(
            "WARNING: AI_API_KEY ёфт нашуд."
        )

    # Render web server
    threading.Thread(
        target=run_web_server,
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
        "FREE CHAT: ON"
    )

    print(
        "TAJIK: ON"
    )

    print(
        "RUSSIAN: ON"
    )

    print(
        "OTHER LANGUAGES: OFF"
    )

    print(
        "MATEO NAME REQUIRED: ON"
    )

    print(
        "===================================="
    )

    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
