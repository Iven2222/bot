import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

TOKEN = os.environ.get("TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

BOT_USERNAME = "testarogbot"  # без @

bans = {}  # {user_id: username}
users = {}  # {user_id: username}


# --- проверка админа ---
def is_admin(user_id):
    return user_id == ADMIN_ID


# --- сообщения ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users[user.id] = user.username
    logging.info(f"Сообщение от {user.id} @{user.username}: {update.message.text}")

    if user.id in bans:
        await update.message.reply_text("🚫 Вы забанены.")
        return

    # проверяем, есть ли получатель
    target_id = context.user_data.get("target")

    if not target_id:
        await update.message.reply_text("❌ Используй ссылку, чтобы отправить сообщение.")
        return

    username = user.username if user.username else "без username"

    # если получатель — админ → показываем отправителя
    if target_id == ADMIN_ID:
        text = (
            f"📩 Новое сообщение:\n\n{update.message.text}\n\n"
            f"👤 @{username}\n🆔 {user.id}"
        )
    else:
        text = f"📩 Новое анонимное сообщение:\n\n{update.message.text}"

    # отправляем сообщение
    await context.bot.send_message(
        chat_id=target_id,
        text=text
    )

    await update.message.reply_text("✅ Отправлено")


# --- команда start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users[user.id] = user.username
    logging.info(f"Новый пользователь: {user.id} @{user.username}")

    # если есть аргумент (переход по ссылке)
    if context.args:
        target_id = context.args[0]
        context.user_data["target"] = int(target_id)

        await update.message.reply_text("✉️ Напиши сообщение, и я анонимно отправлю его пользователю.")
        return

    # обычный старт
    link = f"https://t.me/{BOT_USERNAME}?start={user.id}"

    await update.message.reply_text(
        "👋 Привет, я бот для анонимных сообщений! Поделись этой ссылкой чтобы получать сообщения 😃\n\n"
        f"{link}"
    )


# --- команда admin ---
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только админ может использовать эту команду.")
        return

    text = (
        "⚙️ Админ команды:\n\n"
        "/ban username — забанить\n"
        "/unban username — разбанить\n"
        "/banlist — список банов\n"
    )

    await update.message.reply_text(text)


# --- бан ---
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только админ может использовать эту команду.")
        return

    if not context.args:
        await update.message.reply_text("Используй: /ban username")
        return

    username = context.args[0].replace("@", "")

    for user_id, uname in users.items():
        if uname == username:
            bans[user_id] = username

            await context.bot.send_message(
                chat_id=user_id,
                text="🚫 Вы были забанены"
            )

            await update.message.reply_text("✅ Забанен")
            return

    await update.message.reply_text("Не найден")


# --- разбан ---
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только админ может использовать эту команду.")
        return

    if not context.args:
        await update.message.reply_text("Используй: /unban username")
        return

    username = context.args[0].replace("@", "")

    for user_id, uname in list(bans.items()):
        if uname == username:
            del bans[user_id]

            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Вы разбанены"
            )

            await update.message.reply_text("Разбанен")
            return

    await update.message.reply_text("Не найден в бане")


# --- список ---
async def banlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Только админ может использовать эту команду.")
        return

    if not bans:
        await update.message.reply_text("Список пуст")
        return

    text = "🚫 Банлист:\n\n"
    for username in bans.values():
        text += f"@{username}\n"

    await update.message.reply_text(text)


# --- обработчик ошибок ---
async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Ошибка: {context.error}", exc_info=context.error)
    if update and update.message:
        await update.message.reply_text("⚠️ Произошла ошибка. Попробуй ещё раз.")


# --- запуск ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_error_handler(error_handler)

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("banlist", banlist))

print(f"Бот работает... TOKEN задан: {bool(TOKEN)}, ADMIN_ID: {ADMIN_ID}")
app.run_polling()
