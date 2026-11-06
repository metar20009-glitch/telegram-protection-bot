
import os
import time
from collections import defaultdict, deque

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

MAX_MESSAGES = 5
TIME_WINDOW = 8

user_messages = defaultdict(deque)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡 أهلاً بك في بوت الحماية\n"
        "أنا بوت حماية المجموعات من السبام والتفليش.\n"
        "اكتب /help لمعرفة الأوامر."
    )


async def help_command(update: Update, context):
    await update.message.reply_text(
        "🛡 أوامر البوت:\n"
        "/start - تشغيل البوت\n"
        "/help - المساعدة\n"
        "/status - حالة الحماية"
    )


async def status(update: Update, context):
    await update.message.reply_text(
        "🟢 الحماية تعمل\n"
        "⚡ مكافحة السبام مفعلة\n"
        "🛡 مراقبة الرسائل مفعلة"
    )


async def is_admin(update, context):
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id,
            update.effective_user.id
        )
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or not chat:
        return

    if await is_admin(update, context):
        return

    now = time.monotonic()
    key = (chat.id, user.id)
    messages = user_messages[key]

    while messages and now - messages[0] > TIME_WINDOW:
        messages.popleft()

    messages.append(now)

    if len(messages) > MAX_MESSAGES:
        try:
            await message.delete()
            messages.clear()
            await context.bot.send_message(
                chat.id,
                f"⚠️ تم رصد إرسال متكرر من {user.first_name}"
            )
        except Exception:
            pass


async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN غير مضبوط")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))

    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & ~filters.COMMAND,
            protect
        )
    )

    print("Protection Bot Started")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await __import__("asyncio").Event().wait()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
  
