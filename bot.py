import os
import tempfile
import logging
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters
)
from yt_dlp import YoutubeDL

from config import BOT_TOKEN, PAYMENT_PROVIDER_TOKEN, CHANNEL_ID

# Настроим логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Существующие функции (не трогаем) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="lang_uz")],
    ]
    await update.message.reply_text(
        "🌐 <b>Выберите язык / Tilni tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def lang_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    lang = update.callback_query.data.split("_")[1]
    context.user_data['lang'] = lang
    keyboard = [[InlineKeyboardButton(s['title'], callback_data=f"svc_{i}")] for i, s in enumerate(services)]
    await update.callback_query.edit_message_text(
        "👇 <b>Выберите услугу / Xizmatni tanlang:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def pay_click(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def pay_manual(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def pay_payme(update: Update, context: ContextTypes.DEFAULT_TYPE): pass
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE): await update.pre_checkout_query.answer(ok=True)
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE): pass

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


# --- Новая функция: /download ---
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return
    if not context.args:
        return await msg.reply_text("Использование: /download <URL видео>")
    url = context.args[0]

    await msg.reply_text("⏳ Скачиваю видео, подожди…")
    with tempfile.TemporaryDirectory() as tmpdir:
        opts = {
            'format': 'bestvideo+bestaudio/best',
            'quiet': True,
            'outtmpl': os.path.join(tmpdir, '%(id)s.%(ext)s')
        }
        cookies = os.environ.get('YT_COOKIES_FILE')
        if cookies and os.path.exists(cookies):
            opts['cookiefile'] = cookies
        try:
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                fp = ydl.prepare_filename(info)
            with open(fp, 'rb') as f:
                await msg.reply_video(f)
        except Exception as e:
            logger.error(f"Ошибка скачивания: {e}")
            await msg.reply_text("❌ Не удалось скачать видео. Проверьте ссылку и попробуйте снова.")

# --- Entry point ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    # сброс webhooks и старых апдейтов
    app.bot.delete_webhook(drop_pending_updates=True)
    # существующие хэндлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_select, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(service_selected, pattern="^svc_"))
    app.add_handler(CallbackQueryHandler(back_to_services, pattern="^back_to_services$"))
    app.add_handler(CallbackQueryHandler(pay_click, pattern="^pay_click_"))
    app.add_handler(CallbackQueryHandler(pay_manual, pattern="^pay_manual_"))
    app.add_handler(CallbackQueryHandler(pay_payme, pattern="^pay_payme_"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    # новый хэндлер
    app.add_handler(CommandHandler('download', download_video))
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
