import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Функция для сохранения заметок в файл
def save_notes_to_file(user_notes):
    with open("notes.json", "w") as file:
        json.dump(user_notes, file, indent=4)

# Функция для чтения заметок из файла
def read_notes_from_file():
    try:
        with open("notes.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Загрузка заметок из файла при запуске бота
user_notes = read_notes_from_file()

# Клавиатура для удаления заметки
def delete_note_keyboard(notes):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for note in notes:
        keyboard.add(types.InlineKeyboardButton(f"🗑{note['date']}", callback_data=f"delete_note_{note['date']}"))
    return keyboard

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("Создать заметку"))
    keyboard.add(types.KeyboardButton("Открыть все заметки📂"))
    
    await message.answer("Привет! Я бот для записи заметок.", reply_markup=keyboard)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer('Бот позволяет создавать и сохранять заметки, для создания и порспмотра ваших заметок нажмити кнопки на клавиатуре')

@dp.message_handler(lambda message: message.text.lower() == "создать заметку")
async def add_note_command(message: types.Message):
    await message.answer("Введите заметку:")
    user_id = str(message.from_user.id)
    user_notes[user_id] = user_notes.get(user_id, [])  # Создаем запись для заметок пользователя

@dp.message_handler(lambda message: message.text.lower() == "открыть все заметки📂")
async def read_notes(message: types.Message):
    user_id = str(message.from_user.id)
    notes = user_notes.get(user_id)
    if notes:
        notes_text = "Ваши заметки:\n"
        for note in notes:
            notes_text += f"Дата: {note['date']}\nЗаметка: {note['note']}\n\n"
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("Назад", callback_data="back"))
        keyboard.add(types.InlineKeyboardButton("Удалить заметку🗑", callback_data="delete"))
        await message.answer(notes_text, reply_markup=keyboard)
    else:
        await message.answer("У вас пока нет заметок.")

@dp.callback_query_handler(lambda query: query.data.startswith('delete_note_'))
async def delete_note_callback(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    date_to_delete = callback_query.data.split('_')[-1]
    notes = user_notes.get(user_id)
    notes_text = "Ваши заметки:\n"
    for note in notes:
        notes_text += f"Дата: {note['date']}\nЗаметка: {note['note']}\n\n"
    if notes:
        for i, note in enumerate(notes):
            if note['date'] == date_to_delete:
                del user_notes[user_id][i]
                save_notes_to_file(user_notes)
                await callback_query.answer("Заметка удалена🗑")
                notes = user_notes.get(user_id)
                keyboard = delete_note_keyboard(notes)
                keyboard.add(types.InlineKeyboardButton("Назад", callback_data="back"))
                await callback_query.message.edit_text(notes_text, reply_markup=keyboard)
                return
    await callback_query.answer("Заметка не найдена")

@dp.callback_query_handler(lambda query: query.data == 'back')
async def back_callback(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    notes = user_notes.get(user_id)
    if notes:
        notes_text = "Ваши заметки:\n"
        for note in notes:
            notes_text += f"Дата: {note['date']}\nЗаметка: {note['note']}\n\n"
        keyboard = delete_note_keyboard(notes)
        keyboard.add(types.InlineKeyboardButton("Назад", callback_data="back"))
        await callback_query.message.edit_text(notes_text, reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("У вас пока нет заметок.")

@dp.callback_query_handler(lambda query: query.data == 'delete')
async def delete_menu_callback(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    notes = user_notes.get(user_id)
    if notes:
        notes_text = "\n"
        for note in notes:
            notes_text += f"Дата: {note['date']}\nЗаметка: {note['note']}\n\n"
    keyboard = delete_note_keyboard(notes)
    keyboard.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    await callback_query.message.edit_text(f"Какую заметку удалять?🗑\n{notes_text}", reply_markup=keyboard)

@dp.message_handler()
async def save_note(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in user_notes:
        user_notes[user_id].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": message.text
        })
        save_notes_to_file(user_notes)  # Сохраняем заметки в файл
        await message.answer("Заметка сохранена!")
    else:
        await message.answer("Чтобы начать новую заметку, введите /note.")

if __name__ == '__main__':
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(dp.start_polling())
    loop.run_forever()
