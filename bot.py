import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
import asyncio

# --- ENV ---
TOKEN = os.environ.get("TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# --- данные ---
users = {}
banned = {}

# --- AI ---
async def ai_response(prompt: str) -> str:
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

# --- команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users[user.id] = user.username or f"id{user.id}"

    if context.args:
        context.user_data["target"] = context.args[0]
        await update.message.reply_text("Напиши сообщение, я отправлю его анонимно.")
        return

    username = context.bot.username
    link = f"https://t.me/{username}?start={user.id}"

    await update.message.reply_text(
        f"Привет! Вот твоя ссылка:\n\n{link}"
    )

async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user

    if sender.id in banned:
        return

    if "target" in context.user_data:
        target = context.user_data["target"]
        text = update.message.text

        await context.bot.send_message(
            chat_id=target,
            text=f"📩 Анонимное сообщение:\n\n{text}"
        )

        await update.message.reply_text("Отправлено.")
        del context.user_data["target"]

async def ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /ai вопрос")
        return

    prompt = " ".join(context.args)
    answer = await ai_response(prompt)
    await update.message.reply_text(answer)

# --- Telegram ---
app_telegram = ApplicationBuilder().token(TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(CommandHandler("ai", ai))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_message))

# --- Flask ---
flask_app = Flask(__name__)

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, app_telegram.bot)
    # запускаем обработку асинхронно через asyncio
    import asyncio
    asyncio.create_task(app_telegram.process_update(update))
    return "ok"

@flask_app.route("/")
def index():
    return "Bot is running"

# --- Setup webhook и запуск Flask ---
async def setup_webhook():
    await app_telegram.initialize()
    await app_telegram.bot.set_webhook(
        url=f"https://bot-sq2i.onrender.com/{TOKEN}"
    )

if __name__ == "__main__":
    # Инициализация webhook
    asyncio.run(setup_webhook())
    
    # Запуск Flask
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
