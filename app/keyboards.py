# Импорт функций из библиотек
from aiogram.types import (ReplyKeyboardMarkup,
                           KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

#Кнопки для подтверждения отправки сообщений во все чаты
keyboard_send_mess = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Отправить', callback_data='send'),
     InlineKeyboardButton(text='Отменить', callback_data='cancel')],

])