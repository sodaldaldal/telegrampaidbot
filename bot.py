from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery, Invoice
)
import json
import time
from config import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID, PAYMENT_PROVIDER_TOKEN

app = Client("paid_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Купить доступ на 30 дней", callback_data="buy_access")]
    ])
    await message.reply(
        "👋 Добро пожаловать! Здесь ты можешь получить доступ в закрытый канал на 30 дней.",
        reply_markup=keyboard
    )

@app.on_callback_query(filters.regex("buy_access"))
async def buy_access(client, callback_query):
    await client.send_invoice(
        chat_id=callback_query.from_user.id,
        title="Доступ в канал на 30 дней",
        description="После оплаты вы получите доступ в закрытый Telegram-канал.",
        payload="monthly_access",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="RUB",
        prices=[LabeledPrice("Подписка", 19900)],
        start_parameter="access-subscription",
    )
    await callback_query.answer()

@app.on_pre_checkout_query()
async def pre_checkout(client, query: PreCheckoutQuery):
    await query.answer(ok=True)

@app.on_message(filters.successful_payment)
async def successful_payment(client, message: Message):
    user_id = message.from_user.id
    users = load_users()
    users[str(user_id)] = int(time.time()) + 30 * 24 * 60 * 60
    save_users(users)

    try:
        await client.add_chat_members(CHANNEL_ID, [user_id])
        await message.reply("✅ Спасибо за оплату! Доступ выдан на 30 дней.")
    except Exception as e:
        await message.reply(f"❌ Ошибка при добавлении в канал: {e}")

@app.on_message(filters.command("check"))
async def check(client, message: Message):
    user_id = message.from_user.id
    users = load_users()
    expire = users.get(str(user_id))

    if expire and expire > int(time.time()):
        remaining = int((expire - time.time()) / 86400)
        await message.reply(f"✅ У тебя есть доступ. Осталось {remaining} дней.")
    else:
        await message.reply("⛔ У тебя нет доступа или он истёк.")

app.run()
