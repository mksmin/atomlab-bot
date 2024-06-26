# Импорт библиотек
import asyncio
import logging
import os

# Импорт функций из библиотек
from aiogram import Bot, Dispatcher

# Импорт из файлов
from app.handlers import router
from app.adminpanel import adm_r
from config.config import get_tokens
from app.database.models import async_main


# Функция для запуска бота
async def main():
    await async_main()
    # Собираем все для запуска бота
    bot_TOKEN = await get_tokens('TOKEN')
    bot = Bot(token=bot_TOKEN)
    dp = Dispatcher()
    dp.include_routers(adm_r, router)
    await bot.delete_webhook(drop_pending_updates=True) #Пропускаем накопленные сообщения
    await dp.start_polling(bot)

# Запускаем бота при условии запуска run плюс включаем логгирование
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')

