from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def back_button():
    """
    Создает клавиатуру с кнопкой "Назад".
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def countries_keyboard(countries):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=country)] for country in countries],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def regions_keyboard(regions):
    """
    Генерация клавиатуры для списка уникальных регионов.
    """
    unique_regions = list(set(regions))  # Убираем дубликаты
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=region)] for region in unique_regions],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def vacancies_keyboard(vacancies):
    """
    Генерация клавиатуры для списка уникальных вакансий.
    """
    unique_vacancies = list(set(vacancies))  # Убираем дубликаты
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=vacancy)] for vacancy in unique_vacancies],
        resize_keyboard=True,
        one_time_keyboard=True
    )
