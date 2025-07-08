import os
import json
import asyncio
import schedule
import time
import threading
import openai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Мини-роадмап
roadmap = [
    {"day": 1, "theme": "Как работает LLM", "goal": "Понять токены, контекст, параметры"},
    {"day": 2, "theme": "Что такое промпт", "goal": "Узнать структуру и типы промптов"},
    {"day": 3, "theme": "Zero-shot и few-shot", "goal": "Строить краткие и ясные запросы"},
    {"day": 4, "theme": "Chain-of-Thought", "goal": "Уметь задавать пошаговые рассуждения"},
    {"day": 5, "theme": "Температура, топ-p", "goal": "Управлять креативностью модели"},
    {"day": 6, "theme": "Роли и контекст", "goal": "Настраивать поведение ИИ в роли"},
    {"day": 7, "theme": "Инструкции и формат вывода", "goal": "Указывать формат ответа, bullet points, таблицы"},
    {"day": 8, "theme": "Галлюцинации и их причины", "goal": "Научиться их ловить и снижать"},
    {"day": 9, "theme": "Повторяемость промптов", "goal": "Делать стабильные промпты для автоматизации"},
    {"day": 10, "theme": "Тестирование промптов", "goal": "Проверять варианты и находить оптимальный"},
    {"day": 11, "theme": "Ограничения и фильтрация", "goal": "Встраивать защиту от плохих запросов"},
    {"day": 12, "theme": "Многошаговые цепочки", "goal": "Делать промпты, зависящие от предыдущих"},
    {"day": 13, "theme": "Хранение и переиспользование", "goal": "Сохранять шаблоны и создавать библиотеки"},
    {"day": 14, "theme": "Мемный день 🎉", "goal": "Отдохнуть и закрепить материал через мемы и смешные кейсы"},
]

PROGRESS_FILE = "progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"day": 1, "status": {}}

def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)

async def get_meme_quote_from_gpt():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты — гениальный, слегка дерзкий мотивационный коуч."},
                {"role": "user", "content": "Сгенерируй короткую мемно-мотивирующую цитату."}
            ],
            max_tokens=60,
            temperature=1.2,
        )
        return response["choices"][0]["message"]["content"]
    except:
        return "🔥 Даже если мотивация не пришла — ты можешь её сгенерировать сам!"

# Планировщик
async def morning_routine(app):
    progress = load_progress()
    day = progress["day"]
    theme = roadmap[day - 1]["theme"]
    goal = roadmap[day - 1]["goal"]
    yesterday = roadmap[day - 2]["theme"] if day > 1 else "Ты только начинаешь!"

    await app.bot.send_message(chat_id=CHAT_ID, text=(
        f"🌅 Доброе утро, воин знания!\n\n"
        f"🧠 Вчера: *{yesterday}*\n"
        f"🔥 Сегодня: *{theme}*\n"
        f"🎯 Зачем: {goal}\n\n"
        f"⚔️ *Вперёд, Лорд Обучений ждёт от тебя дисциплины!*"
    ), parse_mode="Markdown")

    await app.bot.send_message(chat_id=CHAT_ID, text="🤖 Учение тяжело, но ты не в качалке — ты в битве с ленивым мозгом.")
    meme = await get_meme_quote_from_gpt()
    await app.bot.send_message(chat_id=CHAT_ID, text=f"🤖 {meme}")

async def day_check(app):
    progress = load_progress()
    day = progress["day"]
    status = progress["status"].get(str(day), "не отмечено")

    msg = "✅ Уже учился сегодня. Красава!" if status == "done" else "👀 Ты ещё не сел за учёбу. Напиши /study — и мы это зафиксируем!"
    await app.bot.send_message(chat_id=CHAT_ID, text=msg)

async def evening_motivation(app):
    progress = load_progress()
    total = len(roadmap)
    day = progress["day"]
    await app.bot.send_message(chat_id=CHAT_ID, text=(
        f"🌙 День {day} из {total} завершён.\n"
        f"🔥 Ты не просто начал — ты идёшь до конца. Продолжай!"
    ))
    meme = await get_meme_quote_from_gpt()
    await app.bot.send_message(chat_id=CHAT_ID, text=f"🌌 {meme}")

def start_scheduler(app):
    def run():
        schedule.every().day.at("11:00").do(lambda: asyncio.run(morning_routine(app)))
        schedule.every().day.at("15:00").do(lambda: asyncio.run(day_check(app)))
        schedule.every().day.at("19:00").do(lambda: asyncio.run(evening_motivation(app)))
        while True:
            schedule.run_pending()
            time.sleep(30)

    threading.Thread(target=run, daemon=True).start()

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я — Лорд Обучений. Пиши /study, /progress или /next!")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 Pong!")

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    progress = load_progress()
    today = progress["day"]
    progress["status"][str(today)] = "done"
    save_progress(progress)
    await update.message.reply_text("✅ Учёба зафиксирована!")

async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    progress = load_progress()
    current_day = progress["day"]
    done_days = [int(d) for d, s in progress["status"].items() if s == "done"]
    total_days = len(roadmap)
    theme = roadmap[current_day - 1]["theme"]
    percent = round(len(done_days) / total_days * 100)
    bar = "▓" * (percent // 10) + "░" * (10 - (percent // 10))

    msg = (
        f"📊 Прогресс обучения\n\n"
        f"📅 Сегодня: день {current_day} из {total_days}\n"
        f"🧠 Тема: *{theme}*\n"
        f"✅ Пройдено: {len(done_days)}\n"
        f"📈 Прогресс: `{bar}` {percent}%\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def go_to_next_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    progress = load_progress()
    current_day = progress["day"]
    total_days = len(roadmap)
    progress["status"][str(current_day)] = "done"

    if current_day < total_days:
        progress["day"] += 1
        next_theme = roadmap[progress["day"] - 1]["theme"]
        save_progress(progress)
        await update.message.reply_text(f"⏭ Перешли к дню {progress['day']}!\n🧠 Тема: *{next_theme}*", parse_mode="Markdown")
    else:
        await update.message.reply_text("🎉 Всё пройдено! Ты молодец!")

# Main
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("study", mark_done))
    app.add_handler(CommandHandler("progress", show_progress))
    app.add_handler(CommandHandler("next", go_to_next_day))

    start_scheduler(app)
    print("✅ Бот запущен.")
    await app.run_polling()

# Запуск
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
