from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

TOKEN = "8669068486:AAH6hc44XeJBJi2hdcWrBPipc_zFhBEhT38"
ADMIN_ID = 5129264309

OPENAI_API_KEY = "твой_openai_api_key"
openai.api_key = OPENAI_API_KEY

users = {}  # словарь: user_id -> username
banned = {}  # словарь: user_id -> username

# --- AI-функция ---
async def ai_response(prompt: str) -> str:
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

# --- Старт ---
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
        f"Привет! Я бот для анонимных сообщений. Держи свою ссылку для анонимных сообщений:\n\n{link}"
    )

# --- Анонимные сообщения ---
async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user

    if sender.id in banned:
        return

    if "target" in context.user_data:
        target = context.user_data["target"]
        text = update.message.text

        await context.bot.send_message(
            chat_id=target,
            text=f"📩 Тебе пришло анонимное сообщение:\n\n{text}"
        )

        username = sender.username
        if username:
            username = f"@{username}"
        else:
            username = "нет username"

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Новое анонимное сообщение\n\n"
                 f"Отправитель: {username}\n"
                 f"ID: {sender.id}\n\n"
                 f"Текст:\n{text}"
        )

        await update.message.reply_text("Сообщение отправлено анонимно.")
        del context.user_data["target"]

# --- Админ ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text(
            "Извините, вы не администратор бота! "
            "Администратор может банить людей."
        )
        return

    await update.message.reply_text(
        "Админ панель:\n"
        "/ban username_or_id - забанить пользователя\n"
        "/unban username_or_id - разбанить пользователя\n"
        "/banned - список забаненных пользователей"
    )

# --- Бан по ID или username с уведомлением ---
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Используй: /ban username_or_id")
        return

    target = context.args[0]

    # ищем по ID или username
    user_id = None
    if target.isdigit():
        user_id = int(target)
    else:
        for uid, uname in users.items():
            if uname == target.replace("@", ""):
                user_id = uid
                break

    if not user_id:
        await update.message.reply_text("Пользователь не найден.")
        return

    banned[user_id] = users.get(user_id, f"id{user_id}")

    # уведомление пользователя
    try:
        await context.bot.send_message(user_id, "⚠️ Вы были забанены администратором.")
    except:
        pass

    await update.message.reply_text(f"Пользователь {banned[user_id]} забанен.")

# --- Разбан с уведомлением ---
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Используй: /unban username_or_id")
        return

    target = context.args[0]

    user_id = None
    if target.isdigit():
        user_id = int(target)
    else:
        for uid, uname in banned.items():
            if uname == target.replace("@", ""):
                user_id = uid
                break

    if not user_id or user_id not in banned:
        await update.message.reply_text("Пользователь не найден в списке банов.")
        return

    uname = banned.pop(user_id)

    # уведомление пользователя
    try:
        await context.bot.send_message(user_id, "✅ Вы были разбанены администратором.")
    except:
        pass

    await update.message.reply_text(f"Пользователь {uname} разбанен.")

# --- Список забаненных ---
async def banned_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not banned:
        await update.message.reply_text("Список банов пуст.")
        return

    text = "Забаненные пользователи:\n"
    for uid, uname in banned.items():
        text += f"{uname} (ID: {uid})\n"

    await update.message.reply_text(text)

# --- AI для всех ---
async def ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /ai твой вопрос")
        return

    prompt = " ".join(context.args)
    answer = await ai_response(prompt)
    await update.message.reply_text(answer)

# --- Регистрация хэндлеров ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("banned", banned_list))
app.add_handler(CommandHandler("ai", ai))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_message))

print("Бот запущен...")
app.run_polling()
