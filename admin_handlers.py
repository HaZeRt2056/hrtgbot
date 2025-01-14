import sqlite3
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# Состояния для админки
class AdminState(StatesGroup):
    password_check = State()
    choosing_country = State()
    choosing_action = State()
    choosing_region = State()
    managing_regions = State()
    managing_vacancies = State()
    adding_description = State()

ADMIN_PASSWORD = "0"  # Пароль для входа в админку

def with_back_button(buttons):
    """
    Добавляет кнопку "Назад" ко всем клавиатурам.
    """
    buttons.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

# Команда /admin
@router.message(F.text == "/admin")
async def admin_start(message: Message, state: FSMContext):
    await state.set_state(AdminState.password_check)
    await message.answer("Введите пароль для доступа к админке:")

# Проверка пароля
@router.message(AdminState.password_check)
async def check_password(message: Message, state: FSMContext):
    if message.text == ADMIN_PASSWORD:
        conn = sqlite3.connect("bot_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM countries")
        countries = [row[0] for row in cursor.fetchall()]
        conn.close()

        await state.set_state(AdminState.choosing_country)
        await message.answer(
            "Выберите страну для управления:",
            reply_markup=with_back_button([[KeyboardButton(text=country)] for country in countries])
        )
    else:
        await message.answer("Неверный пароль. Попробуйте снова.")

# Выбор страны
@router.message(AdminState.choosing_country)
async def admin_choose_country(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.set_state(AdminState.password_check)
        await message.answer("Введите пароль для доступа к админке:")
        return

    selected_country = message.text
    await state.update_data(country=selected_country)

    await state.set_state(AdminState.choosing_action)
    await message.answer(
        "Выберите, что вы хотите сделать:",
        reply_markup=with_back_button([
            [KeyboardButton(text="Управление регионами")],
            [KeyboardButton(text="Управление вакансиями")]
        ])
    )

# Управление регионами
@router.message(F.text == "Управление регионами", AdminState.choosing_action)
async def manage_regions(message: Message, state: FSMContext):
    data = await state.get_data()
    country = data.get("country")

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT name
        FROM regions
        WHERE country_id = (SELECT id FROM countries WHERE name = ?)
    """, (country,))
    regions = [row[0] for row in cursor.fetchall()]
    conn.close()

    if regions:
        regions_text = "\n".join([f"{idx + 1}. {region}" for idx, region in enumerate(regions)])
        await message.answer(
            f"Регионы в стране {country}:\n{regions_text}\n\n"
            "Введите номер региона для удаления или введите название нового региона для добавления:",
            reply_markup=with_back_button([[KeyboardButton(text=region)] for region in regions])
        )
    else:
        await message.answer(
            f"В стране {country} пока нет регионов. Введите название нового региона для добавления:",
            reply_markup=with_back_button([])
        )

    await state.set_state(AdminState.managing_regions)

# Добавление и удаление региона
@router.message(AdminState.managing_regions)
async def manage_regions_handler(message: Message, state: FSMContext):
    if message.text == "Назад":
        await admin_choose_country(message, state)
        return

    user_input = message.text
    data = await state.get_data()
    country = data.get("country")

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()

    if user_input.isdigit():
        region_index = int(user_input) - 1
        cursor.execute("""
            SELECT DISTINCT name
            FROM regions
            WHERE country_id = (SELECT id FROM countries WHERE name = ?)
        """, (country,))
        regions = [row[0] for row in cursor.fetchall()]

        if 0 <= region_index < len(regions):
            region_name = regions[region_index]
            cursor.execute("DELETE FROM regions WHERE name = ?", (region_name,))
            conn.commit()
            await message.answer(f"Регион '{region_name}' успешно удалён.")
        else:
            await message.answer("Неверный номер региона. Попробуйте снова.")
    else:
        # Добавление нового региона
        region_name = user_input
        cursor.execute("""
            SELECT 1 FROM regions
            WHERE name = ? AND country_id = (SELECT id FROM countries WHERE name = ?)
        """, (region_name, country))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO regions (name, country_id)
                SELECT ?, id FROM countries WHERE name = ?
            """, (region_name, country))
            conn.commit()
            await message.answer(f"Регион '{region_name}' успешно добавлен.")
        else:
            await message.answer(f"Регион '{region_name}' уже существует.")

    conn.close()
    await manage_regions(message, state)

# Управление вакансиями
@router.message(F.text == "Управление вакансиями", AdminState.choosing_action)
async def manage_vacancies_start(message: Message, state: FSMContext):
    data = await state.get_data()
    country = data.get("country")

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT name
        FROM regions
        WHERE country_id = (SELECT id FROM countries WHERE name = ?)
    """, (country,))
    regions = [row[0] for row in cursor.fetchall()]
    conn.close()

    if regions:
        await state.set_state(AdminState.choosing_region)
        await message.answer(
            "Выберите регион для управления вакансиями:",
            reply_markup=with_back_button([[KeyboardButton(text=region)] for region in regions])
        )
    else:
        await message.answer("В этой стране пока нет доступных регионов.")

# Выбор региона для управления вакансиями
@router.message(AdminState.choosing_region)
async def admin_choose_region(message: Message, state: FSMContext):
    if message.text == "Назад":
        await admin_choose_country(message, state)
        return

    selected_region = message.text
    await state.update_data(region=selected_region)

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.name, rv.is_active
        FROM vacancies v
        JOIN region_vacancy rv ON v.id = rv.vacancy_id
        WHERE rv.region_id = (SELECT id FROM regions WHERE name = ?)
    """, (selected_region,))
    vacancies = cursor.fetchall()
    conn.close()

    if vacancies:
        vacancies_text = "\n".join(
            [f"{idx + 1}. {vacancy[0]} ({'Доступна' if vacancy[1] else 'Скрыта'})"
             for idx, vacancy in enumerate(vacancies)]
        )
        await message.answer(
            f"Доступные вакансии в регионе {selected_region}:\n{vacancies_text}\n\n"
            "Введите номер вакансии для изменения статуса или название новой вакансии для добавления:",
            reply_markup=with_back_button([])
        )
    else:
        await message.answer(
            f"В регионе {selected_region} пока нет вакансий. Введите название новой вакансии для добавления:",
            reply_markup=with_back_button([])
        )

    await state.set_state(AdminState.managing_vacancies)

# Управление вакансиями (добавление/изменение)
@router.message(AdminState.managing_vacancies)
async def manage_vacancies(message: Message, state: FSMContext):
    if message.text == "Назад":
        await manage_vacancies_start(message, state)
        return

    user_input = message.text
    data = await state.get_data()
    selected_region = data.get("region")

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()

    if user_input.isdigit():
        # Изменение статуса вакансии
        vacancy_index = int(user_input) - 1
        cursor.execute("""
            SELECT v.id, rv.is_active
            FROM vacancies v
            JOIN region_vacancy rv ON v.id = rv.vacancy_id
            WHERE rv.region_id = (SELECT id FROM regions WHERE name = ?)
        """, (selected_region,))
        vacancies = cursor.fetchall()

        if 0 <= vacancy_index < len(vacancies):
            vacancy_id, current_status = vacancies[vacancy_index]
            new_status = not current_status  # Меняем статус
            cursor.execute("""
                UPDATE region_vacancy
                SET is_active = ?
                WHERE region_id = (SELECT id FROM regions WHERE name = ?)
                AND vacancy_id = ?
            """, (new_status, selected_region, vacancy_id))
            conn.commit()

            await message.answer(
                f"Статус вакансии изменён. Теперь она {'доступна' if new_status else 'скрыта'}."
            )
        else:
            await message.answer("Неверный номер вакансии. Попробуйте снова.")
    else:
        # Добавление новой вакансии
        new_vacancy_name = user_input

        cursor.execute("SELECT id FROM vacancies WHERE name = ?", (new_vacancy_name,))
        vacancy = cursor.fetchone()

        if not vacancy:
            # Добавление новой вакансии
            cursor.execute("INSERT INTO vacancies (name) VALUES (?)", (new_vacancy_name,))
            vacancy_id = cursor.lastrowid
        else:
            vacancy_id = vacancy[0]

        # Привязка вакансии к региону
        cursor.execute("""
            INSERT OR IGNORE INTO region_vacancy (region_id, vacancy_id, is_active)
            SELECT r.id, ?, 1
            FROM regions r
            WHERE r.name = ?
        """, (vacancy_id, selected_region))
        conn.commit()

        # Сохранение ID вакансии для добавления описания
        await state.update_data(vacancy_id=vacancy_id)

        await message.answer(
            f"Вакансия '{new_vacancy_name}' успешно добавлена и активирована.\n\n"
            "Теперь введите описание для этой вакансии:",
            reply_markup=with_back_button([])
        )
        await state.set_state(AdminState.adding_description)
        conn.close()
        return

    conn.close()

    # Обновление списка вакансий
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.name, rv.is_active
        FROM vacancies v
        JOIN region_vacancy rv ON v.id = rv.vacancy_id
        WHERE rv.region_id = (SELECT id FROM regions WHERE name = ?)
    """, (selected_region,))
    vacancies = cursor.fetchall()
    conn.close()

    if vacancies:
        vacancies_text = "\n".join(
            [f"{idx + 1}. {vacancy[0]} ({'Доступна' if vacancy[1] else 'Скрыта'})"
             for idx, vacancy in enumerate(vacancies)]
        )
        await message.answer(
            f"Доступные вакансии в регионе {selected_region}:\n{vacancies_text}\n\n"
            "Введите номер вакансии для изменения статуса или название новой вакансии для добавления:",
            reply_markup=with_back_button([])
        )
    else:
        await message.answer(f"В регионе {selected_region} пока нет вакансий.")


@router.message(AdminState.adding_description)
async def add_description(message: Message, state: FSMContext):
    data = await state.get_data()
    vacancy_id = data.get("vacancy_id")
    description = message.text

    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()

    # Добавляем описание в таблицу вакансий
    cursor.execute("""
        UPDATE vacancies
        SET description = ?
        WHERE id = ?
    """, (description, vacancy_id))
    conn.commit()
    conn.close()

    await state.set_state(AdminState.managing_vacancies)
    await message.answer("Описание вакансии успешно сохранено.")

