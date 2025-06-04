from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

import os
TOKEN = os.environ["BOT_TOKEN"]

# Список услуг. Поле price хранится в сумах (умноженное на 1000).
services = [
    {
        "title": "Приватный канал",
        "desc": "Доступ к закрытому Telegram-каналу на 30 дней.",
        "price": 500000
    },
    {
        "title": "Бесплатный канал | JafarFilm",
        "desc": "Ссылка на бесплатный канал.",
        "price": 0
    },
    {
        "title": "10$ Adobe + Epidemicsounds",
        "desc": "Аккаунт на месяц с подпиской на Adobe и Epidemicsounds.",
        "price": 1200000
    },
    {
        "title": "5$ ChatGPT Plus + Sora",
        "desc": "Доступ к ChatGPT Plus и Sora.",
        "price": 600000
    },
    {
        "title": "5$ Google Veo 3 Access",
        "desc": "Доступ к Google Veo.",
        "price": 600000
    },
    {
        "title": "Сборник | Бесплатные курсы Контентмейкера",
        "desc": "Полезные бесплатные ресурсы для начинающих.",
        "price": 0
    },
    {
        "title": "Сборник | Платные курсы для Контентмейкера",
        "desc": "Топовые платные курсы по контенту.",
        "price": 300000
    }
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.
    Предлагает выбрать язык (русский или узбекский).
    """
    keyboard = [
        [InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton("O'zbekcha 🇺🇿", callback_data="lang_uz")]
    ]
    await update.message.reply_text(
        "Выберите язык / Tilni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    После того, как пользователь выбрал язык, сохраняем его в context.user_data
    и показываем список услуг.
    """
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]  # "ru" или "uz"
    context.user_data["lang"] = lang

    # Составляем inline-клавиатуру со списком услуг
    keyboard = [
        [InlineKeyboardButton(service["title"], callback_data=f"svc_{i}")]
        for i, service in enumerate(services)
    ]
    await query.edit_message_text(
        "Выберите услугу / Xizmatni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Когда пользователь нажал на одну из услуг (callback_data = "svc_{index}"),
    отправляем ему детальное описание с ценой.
    """
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    svc = services[index]

    # Вот здесь был синтаксический баг: разбитие f-строки «с переносом реального Enter»
    # Безопасно пишем через \n, чтобы Python понимал, где окончание строки.
    message = (
        f"Название: {svc['title']}\n"
        f"Описание: {svc['desc']}\n"
        f"Цена: {svc['price'] // 1000} сум"
    )

    await query.edit_message_text(message)


def main():
    """
    Точка входа: создаём Application, регистрируем хэндлеры и запускаем polling.
    """
    app = ApplicationBuilder().token(TOKEN).build()

    # Обработчик команды /start
    app.add_handler(CommandHandler("start", start))

    # Обработчики нажатий по inline-кнопкам
    app.add_handler(CallbackQueryHandler(lang_select, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(service_selected, pattern="^svc_"))

    app.run_polling()


if __name__ == "__main__":
    main()
