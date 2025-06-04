
async def on_startup(app):
    await app.bot.delete_webhook(drop_pending_updates=True)

# Основной код бота, уже приведён выше (сервисное меню, языки, чек, ручная оплата и т.п.)
# Здесь будет воссоздано — как на предыдущем шаге
