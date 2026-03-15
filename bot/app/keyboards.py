from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from .config import settings

def reply_panel() -> ReplyKeyboardMarkup:
    # Самая стабильная кнопка WebApp
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Открыть склад (WebApp)", web_app=WebAppInfo(url=settings.webapp_url + "?screen=stock"))],
            [KeyboardButton(text="➕ Добавить Б/У (WebApp)", web_app=WebAppInfo(url=settings.webapp_url + "?screen=add"))],
        ],
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False,
    )

def inline_menu() -> InlineKeyboardMarkup:
    # Оставим inline только для отчёта
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Отчёт сегодня", callback_data="today")],
    ])