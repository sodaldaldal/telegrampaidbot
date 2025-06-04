import os
import json
import time
import asyncio
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, PreCheckoutQueryHandler, ContextTypes
)

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))
PAYMENT_PROVIDER_TOKEN = os.environ.get("PAYMENT_PROVIDER_TOKEN")

DB_FILE = "database.json"

def load_users():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Купить доступ на 30 дней", callback_data="buy_access")]
    ])
    await update.message.reply_text(
        "👋 Добро пожаловать! Чтобы получить доступ в закрытый канал, нажми кнопку ниже:",
        reply_markup=keyboard
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    prices = [LabeledPrice("Подписка", 199000)]  # 1990.00 UZS

    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title="Доступ в канал на 30 дней",
        description="После оплаты вы получите автоматический доступ.",
        payload="monthly_access",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="UZS",
        prices=prices,
        start_parameter="access-subscription"
    )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_users()
    users[str(user_id)] = int(time.time()) + 30 * 24 * 60 * 60
    save_users(users)

    try:
        await context.bot.add_chat_members(CHANNEL_ID, [user_id])
        await update.message.reply_text("✅ Спасибо за оплату! Ты добавлен в канал на 30 дней.")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при добавлении: {e}")

async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_users()
    expire = users.get(str(user_id))

    if expire and expire > int(time.time()):
        remaining = int((expire - time.time()) / 86400)
        await update.message.reply_text(f"✅ У тебя есть доступ. Осталось {remaining} дней.")
    else:
        await update.message.reply_text("⛔ У тебя нет доступа или он истёк.")

async def auto_cleanup(bot):
    while True:
        users = load_users()
        now = int(time.time())
        updated = False

        for uid, expire in list(users.items()):
            if expire < now:
                try:
                    await bot.ban_chat_member(CHANNEL_ID, int(uid))
                    await bot.unban_chat_member(CHANNEL_ID, int(uid))
                    print(f"⛔ Удалён пользователь {uid} по окончании доступа.")
                except Exception as e:
                    print(f"Ошибка при удалении {uid}: {e}")
                users.pop(uid)
                updated = True

        if updated:
            save_users(users)

        await asyncio.sleep(1800)  # каждые 30 минут

async def run_cleanup(app):
    await auto_cleanup(app.bot)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_access))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    # Запускаем фоновую задачу вручную
    asyncio.create_task(run_cleanup(app))

    app.run_polling()

if __name__ == "__main__":
    main()
