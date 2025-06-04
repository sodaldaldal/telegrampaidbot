# -*- coding: utf-8 -*-

import json, os, logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, PreCheckoutQueryHandler
from datetime import datetime

logging.basicConfig(level=logging.INFO)
db_path = "database.json"
orders_path = "orders.json"

def load_db():
    try:
        with open(db_path, "r") as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(db_path, "w") as f:
        json.dump(data, f)

def save_order(order):
    try:
        with open(orders_path, "r") as f:
            orders = json.load(f)
    except:
        orders = []
    orders.append(order)
    with open(orders_path, "w") as f:
        json.dump(orders, f, indent=2)

SERVICES = {
    "private": {"title": "Приватный канал", "price": 5000000, "desc": "Доступ на 30 дней."},
    "jafar": {"title": "Бесплатный канал | JafarFilm", "price": 0, "desc": "Просто переходи в канал."},
    "adobe": {"title": "10$ Adobe CC + EpidemicSound", "price": 1200000, "desc": "Доступ на 30 дней."},
    "chatgpt": {"title": "5$ ChatGPT Plus + Sora", "price": 600000, "desc": "Доступ на 30 дней."},
    "veo": {"title": "5$ Google Veo 3 Access", "price": 600000, "desc": "3 аккаунта для тестов."},
    "free_courses": {"title": "Сборник | Бесплатные курсы", "price": 0, "desc": "Полезный архив материалов."},
    "paid_courses": {"title": "Сборник | Платные курсы", "price": 500000, "desc": "Контентмейкерские курсы."}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz")
    ]]
    await update.message.reply_text("Выберите язык / Tilni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = update.callback_query.data.split("_")[1]
    db = load_db()
    db[user_id] = {"lang": lang}
    save_db(db)
    await show_menu(update.callback_query, context)

async def show_menu(update: Update | CallbackQueryHandler, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for key, svc in SERVICES.items():
        keyboard.append([InlineKeyboardButton(svc["title"], callback_data=f"svc_{key}")])
    keyboard.append([
        InlineKeyboardButton("💳 CLICK (скоро)", callback_data="click_placeholder"),
        InlineKeyboardButton("📥 Оплата вручную", callback_data="manual_pay")
    ])
    await update.edit_message_text("📋 Выберите услугу:", reply_markup=InlineKeyboardMarkup(keyboard))

async def service_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = update.callback_query.data.split("_")[1]
    svc = SERVICES.get(key)
    if not svc:
        return await update.callback_query.answer("Неизвестная услуга.")
        text = f"🔹 <b>{svc['title']}</b>\n\n💬 {svc['desc']}\n💰 Цена: {svc['price']//100000} сум"

        text = f"🔹 <b>{svc['title']}</b>\n\n💬 {svc['desc']}\n💰 Цена: {svc['price']//100000} сум"
💰 Цена: {svc['price']//100000} сум"
    keyboard = [
        [InlineKeyboardButton("✅ Купить", callback_data=f"buy_{key}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_menu")]
    ]
    await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_menu(update.callback_query, context)

async def purchase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = update.callback_query.data.split("_")[1]
    svc = SERVICES.get(key)
    if not svc:
        return
    if key == "private":
        prices = [LabeledPrice(svc["title"], svc["price"])]
        await context.bot.send_invoice(
            chat_id=update.effective_user.id,
            title=svc["title"],
            description=svc["desc"],
            payload=key,
            provider_token=os.environ.get("PAYMENT_PROVIDER_TOKEN"),
            currency="UZS",
            prices=prices,
            start_parameter="start"
        )
    else:
        keyboard = [[InlineKeyboardButton("📥 Отправить чек", callback_data="send_receipt")]]
        await update.callback_query.edit_message_text(
            f"🧾 Для услуги <b>{svc['title']}</b> доступна только ручная оплата.

1. Отправьте сумму: {svc['price']//100000} сум
2. Отправьте скриншот чека.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        context.user_data["waiting_receipt"] = key

async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def success_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_order({"user": update.effective_user.id, "service": update.message.successful_payment.invoice_payload, "time": str(datetime.utcnow())})
    await update.message.reply_text("✅ Оплата прошла успешно!")

async def send_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("📤 Пожалуйста, отправьте скриншот или текст чека.")
    context.user_data["awaiting_check"] = True

async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_check"):
        ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
        await context.bot.send_message(ADMIN_ID, f"📥 Новый чек от {update.effective_user.id}")
        if update.message.photo:
            await context.bot.send_photo(ADMIN_ID, photo=update.message.photo[-1].file_id)
        elif update.message.text:
            await context.bot.send_message(ADMIN_ID, text=update.message.text)
        await update.message.reply_text("✅ Чек отправлен на проверку.")
        context.user_data["awaiting_check"] = False

async def on_startup(app):
    await app.bot.delete_webhook(drop_pending_updates=True)

def main():
    app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).post_init(on_startup).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_handler, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(service_info, pattern="^svc_"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_menu$"))
    app.add_handler(CallbackQueryHandler(purchase_handler, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(send_receipt, pattern="^send_receipt$"))
    app.add_handler(CallbackQueryHandler(show_menu, pattern="^manual_pay$"))
    app.add_handler(CallbackQueryHandler(show_menu, pattern="^click_placeholder$"))

    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, success_payment))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_receipt))

    app.run_polling()

if __name__ == "__main__":
    main()
