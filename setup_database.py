from database import init_db, add_country, add_region, add_vacancy, link_vacancy_to_region
import sqlite3  # Не забудьте импортировать sqlite3

# Инициализация базы данных
init_db()

# Добавляем страны
add_country("Россия")
add_country("Кыргызстан")
add_country("Узбекистан")

# Добавляем регионы
add_region("Москва", "Россия")
add_region("Бишкек", "Кыргызстан")
add_region("Ташкент", "Узбекистан")

# Добавляем вакансии с описанием
vacancies = [
    {
        "name": "Разработчик",
        "description": (
            "Разработчик занимается созданием программного обеспечения. "
            "Требуются навыки Python, Django, опыт работы с REST API, Git."
        )
    },
    {
        "name": "Тестировщик",
        "description": (
            "Тестировщик отвечает за качество продукта, проводит ручное и автоматизированное тестирование. "
            "Навыки: Selenium, Pytest, Postman."
        )
    },
    {
        "name": "Менеджер проектов",
        "description": (
            "Менеджер проектов координирует команды, разрабатывает планы и следит за выполнением задач. "
            "Навыки: управление проектами, Agile, Jira."
        )
    },
]

# Функция добавления вакансий с описанием
def add_vacancy_with_description(vacancy_name, description):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()

    # Проверяем, есть ли уже такая вакансия
    cursor.execute("SELECT id FROM vacancies WHERE name = ?", (vacancy_name,))
    vacancy = cursor.fetchone()

    if not vacancy:
        # Добавляем вакансию с описанием, если её нет
        cursor.execute("INSERT INTO vacancies (name, description) VALUES (?, ?)", (vacancy_name, description))
        vacancy_id = cursor.lastrowid
    else:
        vacancy_id = vacancy[0]
        # Обновляем описание, если вакансия уже есть
        cursor.execute("UPDATE vacancies SET description = ? WHERE id = ?", (description, vacancy_id))

    conn.commit()
    conn.close()
    return vacancy_id

# Добавляем вакансии с описанием в базу
for vacancy in vacancies:
    add_vacancy_with_description(vacancy["name"], vacancy["description"])

# Привязываем вакансии к регионам
link_vacancy_to_region("Москва", "Разработчик", True)
link_vacancy_to_region("Москва", "Тестировщик", True)
link_vacancy_to_region("Бишкек", "Менеджер проектов", True)
link_vacancy_to_region("Ташкент", "Тестировщик", True)

print("База данных успешно инициализирована с описаниями вакансий!")
