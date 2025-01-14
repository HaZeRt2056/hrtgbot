import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from admin_handlers import router as admin_router
from database import init_db
from keyboards import countries_keyboard, regions_keyboard, vacancies_keyboard
from configs import *
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest
from aiogram import types  # Убедитесь, что этот импорт добавлен
import requests  # Для выполнения HTTP-запросов



# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния
class JobSearch(StatesGroup):
    choosing_country = State()
    choosing_region = State()
    choosing_vacancy = State()
    entering_name = State()  # Новое состояние для ввода ФИО
    entering_birth_year = State()  # Новое состояние для ввода года рождения
    entering_address = State()  # Ввод адреса проживания
    entering_phone = State()  # Новый шаг
    choosing_gender = State()  # Добавляем состояние выбора пола
    is_student = State()
    choosing_study_form = State()
    choosing_uzbek_level = State()
    choosing_russian_level = State()
    asking_experience = State()
    asking_last_job = State()
    asking_salary = State()
    asking_photo = State()  # Состояние для отправки фото
    asking_source = State()  # Состояние для вопроса об источнике вакансии
    confirming = State() #




# Команда /start
@dp.message(F.text == "/start")
async def start_command(message: Message, state: FSMContext):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM countries")
    countries = [row[0] for row in cursor.fetchall()]
    conn.close()

    await state.set_state(JobSearch.choosing_country)
    await message.answer(
        "Выберите страну:",
        reply_markup=countries_keyboard(countries)
    )


# Выбор страны
@dp.message(JobSearch.choosing_country)
async def choose_country(message: Message, state: FSMContext):
    selected_country = message.text

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT regions.name FROM regions
        JOIN countries ON regions.country_id = countries.id
        WHERE countries.name = ?
    """, (selected_country,))
    regions = [row[0] for row in cursor.fetchall()]
    conn.close()

    if regions:
        # Сохранение выбранной страны
        await state.update_data(country=selected_country)

        await state.set_state(JobSearch.choosing_region)
        regions_keyboard_with_back = regions_keyboard(regions)
        regions_keyboard_with_back.keyboard.append([KeyboardButton(text="⬅ Назад")])  # Добавляем кнопку "Назад"
        await message.answer(
            "Выберите регион:",
            reply_markup=regions_keyboard_with_back
        )
    else:
        await message.answer("В этой стране пока нет доступных регионов.")


# Выбор региона
@dp.message(JobSearch.choosing_region)
async def choose_region(message: Message, state: FSMContext):
    selected_region = message.text

    if selected_region == "⬅ Назад":
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM countries")
        countries = [row[0] for row in cursor.fetchall()]
        conn.close()

        await state.set_state(JobSearch.choosing_country)
        await message.answer(
            "Выберите страну:",
            reply_markup=countries_keyboard(countries)
        )
        return

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.name 
        FROM vacancies v
        JOIN region_vacancy rv ON v.id = rv.vacancy_id
        JOIN regions r ON r.id = rv.region_id
        WHERE r.name = ? AND rv.is_active = 1
    """, (selected_region,))
    vacancies = [row[0] for row in cursor.fetchall()]
    conn.close()

    if vacancies:
        await state.update_data(region=selected_region)

        await state.set_state(JobSearch.choosing_vacancy)
        vacancies_keyboard_with_back = vacancies_keyboard(vacancies)
        vacancies_keyboard_with_back.keyboard.append([KeyboardButton(text="⬅ Назад")])
        await message.answer(
            "Выберите вакансию:",
            reply_markup=vacancies_keyboard_with_back
        )
    else:
        await message.answer("В этом регионе пока нет доступных вакансий.")


# Выбор вакансии
from aiogram.exceptions import TelegramBadRequest

@dp.message(JobSearch.choosing_vacancy)
async def choose_vacancy(message: Message, state: FSMContext):
    selected_vacancy = message.text

    if selected_vacancy == "⬅ Назад":
        user_data = await state.get_data()
        selected_country = user_data.get("country", "")

        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT regions.name FROM regions
            JOIN countries ON regions.country_id = countries.id
            WHERE countries.name = ?
        """, (selected_country,))
        regions = [row[0] for row in cursor.fetchall()]
        conn.close()

        await state.set_state(JobSearch.choosing_region)
        regions_keyboard_with_back = regions_keyboard(regions)
        regions_keyboard_with_back.keyboard.append([KeyboardButton(text="⬅ Назад")])
        await message.answer(
            "Выберите регион:",
            reply_markup=regions_keyboard_with_back
        )
        return

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT description
        FROM vacancies
        WHERE name = ?
    """, (selected_vacancy,))
    vacancy = cursor.fetchone()
    conn.close()

    if vacancy and vacancy[0]:
        description = vacancy[0]
        vacancy_message = await message.answer(
            f"Вы выбрали вакансию: {selected_vacancy}.\n\nОписание:\n{description}",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅ Назад")]],
                resize_keyboard=True
            )
        )
    else:
        vacancy_message = await message.answer(
            f"Вы выбрали вакансию: {selected_vacancy}.\n\nОписание недоступно.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="⬅ Назад")]],
                resize_keyboard=True
            )
        )

    # Сохранение выбранной вакансии и ID сообщения с описанием
    await state.update_data(vacancy=selected_vacancy, vacancy_message_id=vacancy_message.message_id)

    # Запрос ФИО
    fio_message = await message.answer(
        "Введите ФИО (пример: Иванов Иван Иванович):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⬅ Назад")]],
            resize_keyboard=True
        )
    )
    await state.update_data(fio_message_id=fio_message.message_id)
    await state.set_state(JobSearch.entering_name)


@dp.message(JobSearch.entering_name)
async def enter_name(message: Message, state: FSMContext):
    if message.text == "⬅ Назад":
        # Получаем данные из состояния
        user_data = await state.get_data()
        vacancy_message_id = user_data.get("vacancy_message_id")
        fio_message_id = user_data.get("fio_message_id")

        # Удаляем сообщения, если они есть
        try:
            if vacancy_message_id:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=vacancy_message_id)
            if fio_message_id:
                await message.bot.delete_message(chat_id=message.chat.id, message_id=fio_message_id)
        except TelegramBadRequest:
            pass  # Если сообщения уже удалены или недоступны

        # Возвращаемся к выбору вакансии
        selected_region = user_data.get("region")
        if not selected_region:
            await message.answer("Ошибка: Регион не выбран. Попробуйте снова.")
            return

        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.name 
            FROM vacancies v
            JOIN region_vacancy rv ON v.id = rv.vacancy_id
            JOIN regions r ON r.id = rv.region_id
            WHERE r.name = ?
        """, (selected_region,))
        vacancies = [row[0] for row in cursor.fetchall()]
        conn.close()

        await state.set_state(JobSearch.choosing_vacancy)
        vacancies_keyboard_with_back = vacancies_keyboard(vacancies)
        vacancies_keyboard_with_back.keyboard.append([KeyboardButton(text="⬅ Назад")])
        await message.answer(
            "Выберите вакансию:",
            reply_markup=vacancies_keyboard_with_back
        )
        return

    # Если не нажата кнопка "Назад", продолжаем процесс
    await state.update_data(full_name=message.text.strip())

    # Следующий шаг
    await message.answer("Введите ваш год рождения (например, 1990):")
    await state.set_state(JobSearch.entering_birth_year)




@dp.message(JobSearch.entering_name)
async def enter_name(message: Message, state: FSMContext):
    full_name = message.text
    await state.update_data(full_name=full_name)

    await message.answer(
        "Введите ваш год рождения (например, 1990):"
    )
    await state.set_state(JobSearch.entering_birth_year)


@dp.message(JobSearch.entering_birth_year)
async def enter_birth_year(message: Message, state: FSMContext):
    birth_year = message.text
    await state.update_data(birth_year=birth_year)

    await message.answer(
        "Введите адрес проживания (пример: ул. Ленина, дом 12, квартира 34):"
    )
    await state.set_state(JobSearch.entering_address)


@dp.message(JobSearch.entering_address)
async def enter_address(message: Message, state: FSMContext):
    address = message.text
    await state.update_data(address=address)

    # Запрос номера телефона
    await message.answer(
        "Нажмите кнопку ниже, чтобы отправить свой номер телефона 📞",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Отправить номер телефона 📞", request_contact=True)]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(JobSearch.entering_phone)


@dp.message(JobSearch.entering_phone, F.content_type == types.ContentType.CONTACT)
async def enter_phone(message: Message, state: FSMContext):
    if not message.contact:
        await message.answer("Пожалуйста, отправьте ваш номер телефона через кнопку ниже.")
        return

    contact = message.contact
    await state.update_data(phone=contact.phone_number)

    # Запрос выбора пола
    await message.answer(
        "👦/👩 Выберите пол:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👦 Мужчина"), KeyboardButton(text="👩 Женщина")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(JobSearch.choosing_gender)


@dp.message(JobSearch.choosing_gender)
async def choose_gender(message: Message, state: FSMContext):
    gender = message.text.strip()
    valid_options = {"👦 Мужчина": "Мужчина", "👩 Женщина": "Женщина"}

    if gender not in valid_options:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов.")
        return

    await state.update_data(gender=valid_options[gender])

    # Переход к следующему вопросу
    await message.answer(
        "👨‍🎓 Являетесь ли вы учеником, студентом в настоящее время?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(JobSearch.is_student)


# Обрабатываем ответ: является ли студентом
@dp.message(JobSearch.is_student)
async def handle_is_student(message: Message, state: FSMContext):
    answer = message.text
    if answer == "✅ Да":
        await message.answer(
            "📚 Выберите форму обучения:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Очное"), KeyboardButton(text="Вечернее"), KeyboardButton(text="Заочное")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(JobSearch.choosing_study_form)
    elif answer == "❌ Нет":
        await message.answer(
            "🌍 Какой у вас уровень узбекского языка?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Низкий"), KeyboardButton(text="Средний"), KeyboardButton(text="В совершенстве")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(JobSearch.choosing_uzbek_level)
    else:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов.")


# Обрабатываем форму обучения
@dp.message(JobSearch.choosing_study_form)
async def handle_study_form(message: Message, state: FSMContext):
    study_form = message.text
    if study_form in ["Очное", "Вечернее", "Заочное"]:
        await state.update_data(study_form=study_form)

        # Переход к вопросу об уровне узбекского языка
        await message.answer(
            "🌍 Какой у вас уровень узбекского языка?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Низкий"), KeyboardButton(text="Средний"),
                     KeyboardButton(text="В совершенстве")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(JobSearch.choosing_uzbek_level)
    else:
        await message.answer("Пожалуйста, выберите одну из предложенных форм обучения.")


# Обрабатываем уровень узбекского языка
@dp.message(JobSearch.choosing_uzbek_level)
async def handle_uzbek_level(message: Message, state: FSMContext):
    uzbek_level = message.text.strip()
    if uzbek_level in ["Низкий", "Средний", "В совершенстве"]:
        await state.update_data(uzbek_level=uzbek_level)

        # Переход к вопросу об уровне русского языка
        await message.answer(
            "🇷🇺 Какой у вас уровень русского языка?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Низкий"), KeyboardButton(text="Средний"),
                     KeyboardButton(text="В совершенстве")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(JobSearch.choosing_russian_level)
    else:
        await message.answer("Пожалуйста, выберите один из предложенных уровней языка.")


@dp.message(JobSearch.choosing_russian_level)
async def handle_russian_level(message: Message, state: FSMContext):
    russian_level = message.text.strip()
    if russian_level in ["Низкий", "Средний", "В совершенстве"]:
        await state.update_data(russian_level=russian_level)

        # Переход к вопросу об опыте работы
        await message.answer(
            "📊 Какой у вас опыт работы?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="1 год"), KeyboardButton(text="от 1-3 лет"),
                     KeyboardButton(text="более 5 лет")]
                ],
                resize_keyboard=True
            )
        )
        await state.set_state(JobSearch.asking_experience)
    else:
        await message.answer("Пожалуйста, выберите один из предложенных уровней языка.")


@dp.message(JobSearch.asking_experience)
async def handle_experience(message: Message, state: FSMContext):
    experience = message.text.strip()
    if experience in ["1 год", "от 1-3 лет", "более 5 лет"]:
        await state.update_data(experience=experience)

        # Запрос последнего места работы
        await message.answer(
            "❗ Название последнего места работы и причина увольнения? "
            "(Пример: ООО «Работа мечты», Кассир, 2015-2018 гг по своей воле.)",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(JobSearch.asking_last_job)
    else:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов.")


@dp.message(JobSearch.asking_last_job)
async def handle_last_job(message: Message, state: FSMContext):
    last_job = message.text.strip()
    await state.update_data(last_job=last_job)

    # Запрос зарплатных ожиданий
    await message.answer(
        "💰 Укажите ожидаемый уровень заработной платы:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(JobSearch.asking_salary)


@dp.message(JobSearch.asking_salary)
async def handle_salary(message: Message, state: FSMContext):
    salary = message.text.strip()
    await state.update_data(salary=salary)

    # Запрос фото
    await message.answer(
        "👤 Отправьте ваше фото (можно селфи с телефона):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(JobSearch.asking_photo)


@dp.message(JobSearch.asking_photo, F.content_type == types.ContentType.PHOTO)
async def handle_photo(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id  # Получение ID последней отправленной фотографии
    await state.update_data(photo=photo_file_id)

    # Запрос источника информации о вакансии
    await message.answer(
        "❓ Откуда вы узнали о вакансии?",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(JobSearch.asking_source)


@dp.message(JobSearch.asking_source)
async def handle_source(message: Message, state: FSMContext):
    source = message.text.strip()
    await state.update_data(source=source)

    # Получение всех данных из состояния
    collected_data = await state.get_data()

    # Формирование сообщения с данными
    result_message = (
        "Пожалуйста, проверьте введённую информацию:\n\n"
        f"📍 Страна: {collected_data.get('country')}\n"
        f"🌍 Регион: {collected_data.get('region')}\n"
        f"💼 Вакансия: {collected_data.get('vacancy')}\n"
        f"👤 ФИО: {collected_data.get('full_name')}\n"
        f"📞 Телефон: {collected_data.get('phone')}\n"
        f"👦 Пол: {collected_data.get('gender')}\n"
        f"🇺🇿 Уровень узбекского: {collected_data.get('uzbek_level')}\n"
        f"🇷🇺 Уровень русского: {collected_data.get('russian_level')}\n"
        f"📊 Опыт работы: {collected_data.get('experience')}\n"
        f"❗ Последнее место работы: {collected_data.get('last_job')}\n"
        f"💰 Ожидаемая зарплата: {collected_data.get('salary')}\n"
        f"📷 Фото: получено\n"
        f"❓ Источник: {collected_data.get('source')}"
    )

    # Отправка сообщения с кнопками "Да" и "Нет"
    await message.answer(
        result_message,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Да ✅"), KeyboardButton(text="Нет ❌")]
            ],
            resize_keyboard=True
        )
    )
    await state.set_state(JobSearch.confirming)


@dp.message(JobSearch.confirming)
async def handle_confirmation(message: Message, state: FSMContext):
    if message.text == "Да ✅":
        collected_data = await state.get_data()

        # Формирование данных для Trello
        trello_url = "https://api.trello.com/1/cards"
        params = {
            "name": f"{collected_data['region']} - {collected_data['vacancy']}",
            "idList": TRELLO_ID_LIST,
            "key": TRELLO_API_KEY,
            "token": TRELLO_TOKEN,
            "desc": (
                f"ФИО: {collected_data['full_name']}\n"
                f"Год рождения: {collected_data['birth_year']}\n"
                f"Адрес: {collected_data['address']}\n"
                f"Телефон: {collected_data['phone']}\n"
                f"Пол: {collected_data['gender']}\n"
                f"Форма обучения: {collected_data['study_form']}\n"
                f"Уровень узбекского: {collected_data['uzbek_level']}\n"
                f"Уровень русского: {collected_data['russian_level']}\n"
                f"Опыт работы: {collected_data['experience']}\n"
                f"Последнее место работы: {collected_data['last_job']}\n"
                f"Ожидаемая зарплата: {collected_data['salary']}\n"
                f"Источник: {collected_data['source']}\n"
            ),
        }

        try:
            # Создание карточки в Trello
            response = requests.post(trello_url, params=params)
            response.raise_for_status()  # Проверка на ошибки
            card_id = response.json()["id"]  # Получение ID созданной карточки

            # Загрузка фото в Trello
            photo_file_id = collected_data.get("photo")
            if photo_file_id:
                # Скачивание фото из Telegram
                file_info = await bot.get_file(photo_file_id)
                file_path = file_info.file_path
                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                photo_response = requests.get(file_url)
                photo_response.raise_for_status()  # Проверка на ошибки

                # Загрузка фото в Trello
                attachment_url = f"https://api.trello.com/1/cards/{card_id}/attachments"
                files = {
                    "file": ("photo.jpg", photo_response.content)  # Название файла и его содержимое
                }
                attachment_params = {
                    "key": TRELLO_API_KEY,
                    "token": TRELLO_TOKEN
                }
                attach_response = requests.post(attachment_url, params=attachment_params, files=files)
                attach_response.raise_for_status()  # Проверка на ошибки

            await message.answer("Спасибо! Данные и фото успешно сохранены в Trello.", reply_markup=ReplyKeyboardRemove())

            # Возвращение к выбору страны
            await message.answer(
                "Давайте начнем. Выберите страну:",
                reply_markup=countries_keyboard(["Узбекистан", "Россия", "Казахстан"])
            )
            await state.set_state(JobSearch.choosing_country)
        except requests.exceptions.RequestException as e:
            await message.answer(f"Ошибка при сохранении данных в Trello: {e}", reply_markup=ReplyKeyboardRemove())
            print(f"Ошибка Trello API: {e}")
        await state.clear()
    elif message.text == "Нет ❌":
        await message.answer(
            "Давайте начнем сначала. Выберите страну:",
            reply_markup=countries_keyboard(["Узбекистан", "Россия", "Казахстан"])
        )
        await state.set_state(JobSearch.choosing_country)
    else:
        await message.answer("Пожалуйста, выберите 'Да' или 'Нет'.")


# Подключение admin_handlers
dp.include_router(admin_router)

# Запуск бота
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
