from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

import os
TOKEN = os.environ["BOT_TOKEN"]

services = [
    {
        "title": "🔒 Приватный канал",
        "desc": "🔐 Доступ к закрытому Telegram-каналу на 30 дней.",
        "price": 500000
    },
    {
        "title": "🎁 Бесплатный канал | JafarFilm",
        "desc": "📽 Ссылка на бесплатный канал.",
        "price": 0
    },
    {
        "title": "💻 10$ Adobe + Epidemicsounds",
        "desc": "🎨 Аккаунт на месяц с подпиской на Adobe и Epidemicsounds.",
        "price": 1200000
    },
    {
        "title": "🤖 5$ ChatGPT Plus + Sora",
        "desc": "🧠 Доступ к ChatGPT Plus и Sora.",
        "price": 600000
    },
    {
        "title": "📹 5$ Google Veo 3 Access",
        "desc": "🎥 Доступ к Google Veo.",
        "price": 600000
    },
    {
        "title": "📚 Сборник | Бесплатные курсы Контентмейкера",
        "desc": "🆓 Полезные бесплатные ресурсы для начинающих.",
        "price": 0
    },
    {
        "title": "🏆 Сборник | Платные курсы для Контентмейкера",
        "desc": "💎 Топовые платные курсы по контенту.",
        "price": 300000
    }
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.
    Предлагает выбрать язык (русский или узбекский) с эмодзи.
    """
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")]
    ]
    await update.message.reply_text(
        "🌐 <b>Выберите язык / Tilni tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Сохраняем выбранный язык и показываем список услуг с эмодзи.
    """
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
        parse_mode="HTML"
    )

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    При выборе услуги показываем детальную информацию с эмодзи и HTML-оформлением.
    """
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    svc = services[index]

    # Используем HTML-теги и эмодзи внутри текста
    message = (
        f"📌 <b>Название:</b> {svc['title']}\n"
        f"📝 <b>Описание:</b> {svc['desc']}\n"
        f"💰 <b>Цена:</b> {svc['price'] // 1000} сум"
    )

    await query.edit_message_text(
        message,
        parse_mode="HTML"
    )

def main():
    """
    Запуск бота.
    """
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_select, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(service_selected, pattern="^svc_"))

    app.run_polling()

if __name__ == "__main__":
    main()
