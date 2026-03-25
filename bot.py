from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

TOKEN = "8669068486:AAH6hc44XeJBJi2hdcWrBPipc_zFhBEhT38"
ADMIN_ID = 5129264309

bans = {}  # {user_id: username}
users = {}  # {user_id: username}


# --- проверка админа ---
def is_admin(user_id):
    return user_id == ADMIN_ID


# --- сохраняем пользователей ---
async def save_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users[user.id] = user.username


# --- сообщения ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id in bans:
        await update.message.reply_text("🚫 Вы забанены.")
        return

    username = user.username if user.username else "без username"

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Сообщение:\n{update.message.text}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"👤 @{username}\n🆔 {user.id}"
    )

    await update.message.reply_text("✅ Отправлено")


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


# --- запуск ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_user))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("banlist", banlist))

print("Бот работает...")
app.run_polling()
