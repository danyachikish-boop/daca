import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Вставь сюда токен своего бота от @BotFather
TOKEN = "8874034061:AAGtyRHKcSt3nhU7NAGdD_BsW6GK2lLu0Uc"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню с кнопками
def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 ТОП приложений", callback_data="top_apps")],
        [InlineKeyboardButton(text="🔍 Найти мод", callback_data="search_mod")],
        [InlineKeyboardButton(text="❓ Как установить?", callback_data="help_install")]
    ])

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    text = (
        "Привет! 👋 Это официальный бот канала **SafeMod APK**.\n\n"
        "Здесь ты можешь быстро найти лучшие моды и топ приложений. "
        "Выбери нужный раздел в меню ниже:"
    )
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")

# Обработка нажатий на кнопки
@dp.callback_query(F.data == "top_apps")
async def show_top(callback):
    top_text = (
        "🏆 **ТОП-3 мода недели:**\n\n"
        "1. **Brawl Stars (Много денег)** — версия 54.2\n"
        "2. **Minecraft PE (Всё разблокировано)** — версия 1.20\n"
        "3. **Car Parking Multiplayer (Взлом)** — все машины открыты"
    )
    await callback.message.edit_text(top_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "search_mod")
async def search_mod(callback):
    await callback.message.edit_text(
        "🔍 Напиши название игры или приложения прямо в чат, и я поищу его в базе!",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "help_install")
async def help_install(callback):
    help_text = (
        "❓ **Как устанавливать моды:**\n\n"
        "1. Скачай APK-файл из нашего канала.\n"
        "2. Разреши установку из неизвестных источников в настройках телефона.\n"
        "3. Установи игру и наслаждайся взломом!"
    )
    await callback.message.edit_text(help_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    await callback.answer()

# Запуск бота
async def main():
    print("Бот успешно запущен и ждет сообщения...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
