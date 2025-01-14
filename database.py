import sqlite3

DB_NAME = "bot_data.db"

def init_db():
    """
    Инициализация базы данных: создание таблиц, если их нет.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблица для стран
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    # Таблица для регионов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            country_id INTEGER,
            FOREIGN KEY (country_id) REFERENCES countries(id)
        )
    """)

    # Таблица для вакансий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT
        )
    """)

    # Промежуточная таблица "многие-ко-многим" между регионами и вакансиями
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS region_vacancy (
            region_id INTEGER,
            vacancy_id INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (region_id) REFERENCES regions(id),
            FOREIGN KEY (vacancy_id) REFERENCES vacancies(id)
        )
    """)

    conn.commit()
    conn.close()

def add_country(name):
    """
    Добавление страны в базу данных.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO countries (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def add_region(name, country_name):
    """
    Добавление региона в указанную страну.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO regions (name, country_id)
        SELECT ?, id FROM countries WHERE name = ?
    """, (name, country_name))
    conn.commit()
    conn.close()

def add_vacancy(name, description=None):
    """
    Добавление вакансии с описанием.
    Если вакансия уже существует, обновляет её описание.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM vacancies WHERE name = ?", (name,))
    vacancy = cursor.fetchone()

    if not vacancy:
        # Добавляем вакансию, если её нет
        cursor.execute("INSERT INTO vacancies (name, description) VALUES (?, ?)", (name, description))
    else:
        # Обновляем описание вакансии
        cursor.execute("UPDATE vacancies SET description = ? WHERE name = ?", (description, name))

    conn.commit()
    conn.close()

def link_vacancy_to_region(region_name, vacancy_name, is_active=True):
    """
    Привязка вакансии к региону, если такая связь ещё не существует.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Проверяем, существует ли уже связь между регионом и вакансией
    cursor.execute("""
        SELECT 1 FROM region_vacancy
        WHERE region_id = (SELECT id FROM regions WHERE name = ?)
        AND vacancy_id = (SELECT id FROM vacancies WHERE name = ?)
    """, (region_name, vacancy_name))
    exists = cursor.fetchone()

    if not exists:
        # Добавляем связь только если её нет
        cursor.execute("""
            INSERT INTO region_vacancy (region_id, vacancy_id, is_active)
            SELECT r.id, v.id, ?
            FROM regions r, vacancies v
            WHERE r.name = ? AND v.name = ?
        """, (is_active, region_name, vacancy_name))

    conn.commit()
    conn.close()



def get_countries():
    """
    Получение списка стран.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM countries")
    countries = [row[0] for row in cursor.fetchall()]
    conn.close()
    return countries

def get_regions_by_country(country_name):
    """
    Получение списка уникальных регионов для указанной страны.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT regions.name
        FROM regions
        JOIN countries ON regions.country_id = countries.id
        WHERE countries.name = ?
    """, (country_name,))
    regions = [row[0] for row in cursor.fetchall()]
    conn.close()
    return regions


def get_vacancies_by_region(region_name):
    """
    Получение списка вакансий и их статуса (доступна/скрыта) для указанного региона.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.name, rv.is_active
        FROM vacancies v
        JOIN region_vacancy rv ON v.id = rv.vacancy_id
        JOIN regions r ON r.id = rv.region_id
        WHERE r.name = ?
    """, (region_name,))
    vacancies = cursor.fetchall()
    conn.close()
    return vacancies

def get_vacancy_description(vacancy_name):
    """
    Получение описания вакансии по названию.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT description FROM vacancies WHERE name = ?", (vacancy_name,))
    vacancy = cursor.fetchone()
    conn.close()
    return vacancy[0] if vacancy else None

def update_vacancy_status(region_name, vacancy_name, is_active):
    """
    Обновление статуса вакансии в конкретном регионе (включена/выключена).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE region_vacancy
        SET is_active = ?
        WHERE region_id = (SELECT id FROM regions WHERE name = ?)
        AND vacancy_id = (SELECT id FROM vacancies WHERE name = ?)
    """, (is_active, region_name, vacancy_name))
    conn.commit()
    conn.close()
