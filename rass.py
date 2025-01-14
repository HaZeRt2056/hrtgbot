import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram import Router
from configs import BOT_TOKEN

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# Состояния для рассылки
class StatesRassilka(StatesGroup):
    choosing_type = State()
    ask_text = State()
    ask_photo = State()
    ask_video = State()
    confirm = State()

# Клавиатуры
def generate_rassilka_buttons():
    buttons = [
        [KeyboardButton(text="Текст")],
        [KeyboardButton(text="Картинка")],
        [KeyboardButton(text="Видео")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def generate_yes_no():
    buttons = [
        [KeyboardButton(text="Да ✅")],
        [KeyboardButton(text="Нет ❌")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Обработчики команды /rassilka
@router.message(Command("rassilka"))
async def start_rassilka(message: Message, state: FSMContext):
    await message.answer(
        "Выберите тип рассылки:",
        reply_markup=generate_rassilka_buttons()
    )
    await state.set_state(StatesRassilka.choosing_type)


# Выбор типа рассылки
@router.message(StatesRassilka.choosing_type)
async def choose_rassilka_type(message: Message, state: FSMContext):
    print("Хэндлер выбора типа рассылки вызван")  # Отладка
    if message.text == "Текст":
        print("Выбран текст для рассылки")  # Отладка
        await message.answer("Напишите текст для рассылки:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(StatesRassilka.ask_text)
    elif message.text == "Картинка":
        print("Выбрана картинка для рассылки")  # Отладка
        await message.answer("Отправьте картинку для рассылки:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(StatesRassilka.ask_photo)
    elif message.text == "Видео":
        print("Выбрано видео для рассылки")  # Отладка
        await message.answer("Отправьте видео для рассылки:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(StatesRassilka.ask_video)
    else:
        print("Неверный выбор")  # Отладка
        await message.answer("Неверный выбор. Попробуйте снова.", reply_markup=generate_rassilka_buttons())

@router.message(StatesRassilka.ask_text)
async def send_text_rassilka(message: Message, state: FSMContext):
    print("Хэндлер рассылки текста вызван")  # Отладка
    text = message.text
    await message.answer(f"Подтвердите рассылку текста:\n\n{text}", reply_markup=generate_yes_no())
    await state.update_data(content=text, content_type="text")
    await state.set_state(StatesRassilka.confirm)





# Рассылка текста
@router.message(F.state == StatesRassilka.ask_text)
async def send_text_rassilka(message: Message, state: FSMContext):
    print("Хэндлер для отправки текста вызван")  # Отладка
    text = message.text
    await message.answer(f"Подтвердите рассылку текста:\n\n{text}", reply_markup=generate_yes_no())
    await state.update_data(content=text, content_type="text")
    await state.set_state(StatesRassilka.confirm)

# Рассылка фото
@router.message(F.state == StatesRassilka.ask_photo, F.content_type == types.ContentType.PHOTO)
async def send_photo_rassilka(message: Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await message.answer_photo(photo, caption="Подтвердите рассылку картинки:", reply_markup=generate_yes_no())
    await state.update_data(content=photo, content_type="photo")
    await state.set_state(StatesRassilka.confirm)

# Рассылка видео
@router.message(F.state == StatesRassilka.ask_video, F.content_type == types.ContentType.VIDEO)
async def send_video_rassilka(message: Message, state: FSMContext):
    video = message.video.file_id
    await message.answer_video(video, caption="Подтвердите рассылку видео:", reply_markup=generate_yes_no())
    await state.update_data(content=video, content_type="video")
    await state.set_state(StatesRassilka.confirm)

# Подтверждение рассылки
@router.message(F.state == StatesRassilka.confirm)
async def confirm_rassilka(message: Message, state: FSMContext):
    data = await state.get_data()
    content = data.get("content")
    content_type = data.get("content_type")

    if message.text == "Да ✅":
        user_ids = await get_all_users()
        for user in user_ids:
            try:
                if content_type == "text":
                    await bot.send_message(user, content)
                elif content_type == "photo":
                    await bot.send_photo(user, content)
                elif content_type == "video":
                    await bot.send_video(user, content)
            except Exception:
                pass
        await message.answer("Рассылка завершена.")
    elif message.text == "Нет ❌":
        await message.answer("Рассылка отменена.")

    await state.finish()

# Пример функции для получения всех пользователей
async def get_all_users():
    # Здесь должна быть реализация для получения всех пользователей из базы данных
    return [123456789, 987654321]  # Заглушка

# Запуск бота
async def main():
    print("Router подключён")
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
