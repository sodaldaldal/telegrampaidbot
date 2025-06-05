import os
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
)

# ------------------------------------------------------------------
# 1) Читаем токены и конфиг из config.py
# ------------------------------------------------------------------
from config import BOT_TOKEN, PAYMENT_PROVIDER_TOKEN, CHANNEL_ID

# ------------------------------------------------------------------
# 2) Описание всех услуг (каждая услуга — title, desc, price в сумах)
#    При необходимости можно дописать для каждой услуги отдельный channel_id,
#    но в данном примере все оплачиваемые услуги ведут в один канал: CHANNEL_ID.
# ------------------------------------------------------------------
services = [
    {
        "title": "🔒 Приватный канал",
        "desc": "🔐 Доступ к закрытому Telegram-каналу на 30 дней.",
        "price": 500000,  # сумма в UZS (500 000 сум)
        "channel_id": CHANNEL_ID,
    },
    {
        "title": "🎁 Бесплатный канал | JafarFilm",
        "desc": "📽 Ссылка на бесплатный канал.",
        "price": 0,
        "channel_id": CHANNEL_ID,
    },
    {
        "title": "💻 10$ Adobe Creative Cloud + Epidemicsounds",
        "desc": "🎨 Аккаунт на месяц с подпиской на Adobe CC и Epidemicsounds.",
        "price": 1200000,  # 1 200 000 сум
        "channel_id": CHANNEL_ID,
    },
    {
        "title": "🤖 5$ ChatGPT Plus + Sora",
        "desc": "🧠 Доступ к ChatGPT Plus и Sora.",
        "price": 600000,
        "channel_id": CHANNEL_ID,
    },
    {
        "title": "📹 5$ Google Veo 3 Access",
        "desc": "🎥 Доступ к Google Veo 3.",
        "price": 600000,
        "channel_id": CHANNEL_ID,
    },
    {
        "title": "📚 Сборник | Бесплатные курсы Контентмейкера",
        "desc": "🆓 Полезные бесплатные ресурсы для начинающих.",
        "price": 0,
        "channel_id": CHANNEL_ID,
    },
    {
        "title": "🏆 Сборник | Платные курсы для Контентмейкера",
        "desc": "💎 Топовые платные курсы по контенту.",
        "price": 300000,
        "channel_id": CHANNEL_ID,
    },
]

# ------------------------------------------------------------------
# 3) /start — показываем выбор языка
# ------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
    ]
    await update.message.reply_text(
        "🌐 <b>Выберите язык / Tilni tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )

# ------------------------------------------------------------------
# 4) Сохраняем язык и выводим меню услуг
# ------------------------------------------------------------------
async def lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]  # "ru" или "uz"
    context.user_data["lang"] = lang

    keyboard = [
        [InlineKeyboardButton(service["title"], callback_data=f"svc_{i}")]
        for i, service in enumerate(services)
    ]
    await query.edit_message_text(
        "👇 <b>Выберите услугу / Xizmatni tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )

# ------------------------------------------------------------------
# 5) При выборе услуги показываем «чек» + кнопки способов оплаты
# ------------------------------------------------------------------
async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    svc = services[index]
    price_sum = svc["price"] // 1000 if svc["price"] else 0  # для отображения “xxx 000 сум”

    invoice_text = (
        "🧾 <b>Чек заказа:</b>\n\n"
        "Выберите способ оплаты ниже ⬇️"
    )

    pay_keyboard = [
        [
            InlineKeyboardButton(
                "💳 Оплатить Click", callback_data=f"pay_click_{index}"
            )
        ],
        [
            InlineKeyboardButton(
                "🏦 Оплата вручную", callback_data=f"pay_manual_{index}"
            )
        ],
        [
            InlineKeyboardButton(
                "📲 Оплата через Payme", callback_data=f"pay_payme_{index}"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Назад к услугам", callback_data="back_to_services"
            )
        ],
    ]

    await query.edit_message_text(
        invoice_text,
        reply_markup=InlineKeyboardMarkup(pay_keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

# ------------------------------------------------------------------
# 6) Возвращение в список услуг
# ------------------------------------------------------------------
async def back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(service["title"], callback_data=f"svc_{i}")]
        for i, service in enumerate(services)
    ]
    await query.edit_message_text(
        "👇 <b>Выберите услугу / Xizmatni tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )

# ------------------------------------------------------------------
# 7) Click—заглушка
# ------------------------------------------------------------------
async def pay_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "ℹ️ <b>Оплата через Click</b> пока недоступна.

"
        "Мы уведомим вас, как только опция заработает!",
        parse_mode="HTML",
    )

# ------------------------------------------------------------------
# 8) Инструкция «Оплата вручную»
# ------------------------------------------------------------------
async def pay_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.split("_")[2])
    svc = services[idx]
    price_sum = svc["price"] // 1000 if svc["price"] else 0

    manual_text = (
        f"🏦 <b>Инструкция по ручной оплате</b>

"
        f"Вы выбрали: <b>{svc['title']}</b> (стоимость <b>{price_sum} 000 сум</b>).

"
        f"1. Переведите <b>{price_sum} 000 сум</b> на один из счетов:
"
        f"   • <b>Номер карты:</b> 1234 5678 9012 3456
"
        f"   • <b>Получатель:</b> Иванов Иван Иванович
"
        f"   • <b>Назначение:</b> Оплата за «{svc['title']}»

"
        f"2. После перевода пришлите скриншот/чек в этот чат.
"
        f"   Наш менеджер проверит платёж и вручную выдаст доступ.

"
        f"Если вопросы — пишите в поддержку: @VashaPodderzhka"
    )

    await query.edit_message_text(manual_text, parse_mode="HTML")

# ------------------------------------------------------------------
# 9) Обработка «Оплата через Payme» (Telegram-инвойс)
# ------------------------------------------------------------------
async def pay_payme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.split("_")[2])
    svc = services[idx]

    # Если цена = 0, выдаём одноразовую ссылку сразу
    if svc["price"] == 0:
        invite_link = await make_one_time_invite_link(context, svc["channel_id"])
        # Отправляем пользователю кнопку
        keyboard = [
            [InlineKeyboardButton("🔗 Перейти в канал", url=invite_link)]
        ]
        await query.edit_message_text(
            "✅ Эта услуга бесплатна. Нажмите кнопку ниже, чтобы войти в канал:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    # Подготовка инвойса
    amount_tiyin = svc["price"] * 100  # переводим сумы в тийины
    title = svc["title"]
    description = svc["desc"]
    payload = f"payload_service_{idx}"
    provider_token = PAYMENT_PROVIDER_TOKEN
    currency = "UZS"
    prices = [LabeledPrice(label=title, amount=amount_tiyin)]

    await query.message.reply_invoice(
        title=title,
        description=description,
        payload=payload,
        provider_token=provider_token,
        currency=currency,
        prices=prices,
        start_parameter=f"start_{idx}",
    )

# ------------------------------------------------------------------
# 10) Функция для генерации одноразовой пригласительной ссылки
# ------------------------------------------------------------------
async def make_one_time_invite_link(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> str:
    """
    Создаёт одноразовую ссылку с member_limit=1 и expire_date через 24 часа.
    Возвращает саму ссылку (invite_link).
    """
    expire_unix = int((datetime.utcnow() + timedelta(hours=24)).timestamp())

    link_obj = await context.bot.create_chat_invite_link(
        chat_id=chat_id,
        expire_date=expire_unix,
        member_limit=1,
    )
    return link_obj.invite_link

# ------------------------------------------------------------------
# 11) pre_checkout_query нужно подтвердить
# ------------------------------------------------------------------
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

# ------------------------------------------------------------------
# 12) После успешной оплаты выдаём одноразовую ссылку-кнопку
# ------------------------------------------------------------------
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment.to_dict()
    chat_id = update.message.chat.id
    payload = payment.get("invoice_payload", "")
    try:
        idx = int(payload.split("_")[-1])
    except (ValueError, IndexError):
        idx = None

    # Если распарсили индекс услуги и у неё есть channel_id
    if idx is not None and 0 <= idx < len(services):
        svc = services[idx]
        channel_id = svc.get("channel_id")
        # Генерируем одноразовую ссылку
        invite_link = await make_one_time_invite_link(context, channel_id)

        # Формируем кнопку «Перейти в канал»
        keyboard = [
            [InlineKeyboardButton("🔗 Перейти в канал", url=invite_link)]
        ]
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"🎉 <b>Платёж принят!</b>

"
                f"Нажмите кнопку ниже, чтобы перейти в приватный канал:"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    # Если payload не распарсился, просто благодарим
    await context.bot.send_message(
        chat_id=chat_id,
        text="🎉 <b>Платёж принят успешно!</b>
Спасибо за покупку. Доступ отправлю вам вручную.",
        parse_mode="HTML",
    )

# ------------------------------------------------------------------
# 13) Основной запуск бота
# ------------------------------------------------------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # /start
    app.add_handler(CommandHandler("start", start))

    # Выбор языка
    app.add_handler(CallbackQueryHandler(lang_select, pattern="^lang_"))

    # Выбор услуги
    app.add_handler(CallbackQueryHandler(service_selected, pattern="^svc_"))

    # Назад к списку услуг
    app.add_handler(CallbackQueryHandler(back_to_services, pattern="^back_to_services$"))

    # Click (заглушка)
    app.add_handler(CallbackQueryHandler(pay_click, pattern="^pay_click_"))

    # Оплата вручную
    app.add_handler(CallbackQueryHandler(pay_manual, pattern="^pay_manual_"))

    # Оплата через Payme
    app.add_handler(CallbackQueryHandler(pay_payme, pattern="^pay_payme_"))

    # pre_checkout_query
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    # Успешная оплата
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    app.run_polling()

if __name__ == "__main__":
    main()