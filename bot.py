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

from config import BOT_TOKEN, PAYMENT_PROVIDER_TOKEN, CHANNEL_ID

import tempfile
import logging
from yt_dlp import YoutubeDL

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


services = [
    {
        "title": "🔒 Приватный канал",
        "desc": "🔐 Доступ к закрытому Telegram-каналу на 30 дней.",
        "price": 500000,
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
        "price": 1200000,
        "channel_id": CHANNEL_ID,
    },
    {
        "title": "🤖 5$ ChatGPT Plus + Sora",
        "desc": "🧠 Доступ к ChatGPT Plus и Sора.",
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


async def lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
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


async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    svc = services[index]
    # если цена в тиынах, то показываем сумму в тысячах сум
    price_sum = svc["price"] // 1000 if svc["price"] else 0

    invoice_text = (
        "🧾 <b>Чек заказа:</b>\n\n"
        "Выберите способ оплаты ниже ⬇️"
    )

    pay_keyboard = [
        [InlineKeyboardButton("💳 Оплатить Click", callback_data=f"pay_click_{index}")],
        [InlineKeyboardButton("🏦 Оплата вручную", callback_data=f"pay_manual_{index}")],
        [InlineKeyboardButton("📲 Оплата через Payme", callback_data=f"pay_payme_{index}")],
        [InlineKeyboardButton("🔙 Назад к услугам", callback_data="back_to_services")],
    ]

    await query.edit_message_text(
        invoice_text,
        reply_markup=InlineKeyboardMarkup(pay_keyboard),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


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


async def pay_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "ℹ️ <b>Оплата через Click</b> пока недоступна.\n\nМы уведомим вас, как только опция заработает!",
        parse_mode="HTML",
    )


async def pay_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.split("_")[2])
    svc = services[idx]
    price_sum = svc["price"] // 1000 if svc["price"] else 0

    manual_text = (
        f"🏦 <b>Инструкция по ручной оплате</b>\n\n"
        f"Вы выбрали: <b>{svc['title']}</b> (стоимость <b>{price_sum} 000 сум</b>).\n\n"
        f"1. Переведите <b>{price_sum} 000 сум</b> на:\n"
        "   • <b>Карта:</b> 1234 5678 9012 3456\n"
        "   • <b>Получатель:</b> Иванов Иван\n"
        f"   • <b>Назначение:</b> Оплата за «{svc['title']}»\n\n"
        "2. Пришлите скрин в чат. Мы проверим и откроем доступ.\n"
        "   Поддержка: @VashaPodderzhka"
    )

    await query.edit_message_text(manual_text, parse_mode="HTML")


async def pay_payme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.split("_")[2])
    svc = services[idx]

    # Если услуга бесплатная, сразу выдаём приглашение
    if svc["price"] == 0:
        invite_link = await make_one_time_invite_link(context, svc["channel_id"])
        keyboard = [[InlineKeyboardButton("🔗 Перейти в канал", url=invite_link)]]
        await query.edit_message_text(
            "✅ Бесплатный доступ. Жмите кнопку ниже:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    amount_tiyin = svc["price"] * 100  # в тиынах
    title = svc["title"]
    description = svc["desc"]
    payload = f"payload_service_{idx}"
    currency = "UZS"
    prices = [LabeledPrice(label=title, amount=amount_tiyin)]

    # Отправляем invoice
    await query.message.reply_invoice(
        title=title,
        description=description,
        payload=payload,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=currency,
        prices=prices,
        start_parameter=f"start_{idx}",
    )


async def make_one_time_invite_link(context, chat_id: int) -> str:
    expire_unix = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
    link_obj = await context.bot.create_chat_invite_link(
        chat_id=chat_id,
        expire_date=expire_unix,
        member_limit=1,
    )
    return link_obj.invite_link


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment.to_dict()
    chat_id = update.message.chat.id
    payload = payment.get("invoice_payload", "")
    try:
        idx = int(payload.split("_")[-1])
    except Exception:
        idx = None

    if idx is not None and 0 <= idx < len(services):
        svc = services[idx]
        invite_link = await make_one_time_invite_link(context, svc["channel_id"])
        keyboard = [[InlineKeyboardButton("🔗 Перейти в канал", url=invite_link)]]
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 <b>Платёж принят!</b>\n\nЖмите кнопку ниже для доступа:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text="🎉 <b>Платёж принят успешно!</b>\nДоступ откроем вручную.",
        parse_mode="HTML",
    )



async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /download <url>
    if not context.args:
        return await update.message.reply_text("Использование: /download <URL видео>")
    url = context.args[0]
    await update.message.reply_text("⏳ Скачиваю видео, подожди…")

    with tempfile.TemporaryDirectory() as tmpdir:
        opts = {
            'format': 'bestvideo+bestaudio/best',
            'quiet': True,
            'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s'),
        }
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)

            with open(filepath, 'rb') as video_file:
                await update.message.reply_video(video_file)
        except Exception as e:
            logger.error(f"Ошибка скачивания: {e}")
            await update.message.reply_text(
                "❌ Не удалось скачать видео. Проверьте ссылку и попробуйте снова."
            )

def main():
    # Строим приложение бота
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем все хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_select, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(service_selected, pattern="^svc_"))
    app.add_handler(CallbackQueryHandler(back_to_services, pattern="^back_to_services$"))
    app.add_handler(CallbackQueryHandler(pay_click, pattern="^pay_click_"))
    app.add_handler(CallbackQueryHandler(pay_manual, pattern="^pay_manual_"))
    app.add_handler(CallbackQueryHandler(pay_payme, pattern="^pay_payme_"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    # Новый хэндлер для скачивания видео
    app.add_handler(CommandHandler('download', download_video))

    # Запускаем polling; drop_pending_updates=True сбросит накопленные апдейты
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
