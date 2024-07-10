# Импорт библиотек
import asyncio
import logging
import os

# Импорт функций из библиотек
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Импорт из файлов
from app.handlers import router
from app.adminpanel import adm_r
from config.config import get_tokens
from app.database.models import async_main


# Функция для запуска бота
async def main():
    # Собираем все для запуска бота
    bot_token = await get_tokens('TOKEN')
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_routers(adm_r, router)
    dp.startup.register(on_startup)
    await bot.delete_webhook(drop_pending_updates=True)  # Пропускаем накопленные сообщения
    await dp.start_polling(bot)


async def on_startup(dispatcher):
    await async_main()
    print('Started database')

# Запускаем бота при условии запуска run.py и включаем логгирование
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)  # Логгирование. Отключить после продакшена
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
