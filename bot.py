import os
import tempfile
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
)
from yt_dlp import YoutubeDL

from config import BOT_TOKEN, PAYMENT_PROVIDER_TOKEN, CHANNEL_ID

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Существующие хэндлеры (start, lang_select, service_selected, back_to_services, pay_click, pay_manual,
# pay_payme, make_one_time_invite_link, precheckout_callback, successful_payment_callback)
# остаются без изменений...

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
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрация существующих хэндлеров оплаты и услуг
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

    # Запуск polling с очисткой старых апдейтов
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
