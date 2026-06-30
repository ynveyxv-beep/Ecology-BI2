# generate_eco_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

def generate_eco_dataset(n_rows=50000):
    """
    Генерирует синтетический датасет для экологического мониторинга
    """
    print(f"🔄 Генерация датасета на {n_rows:,} строк...")
    
    # Списки для случайных значений
    categories = [
        'Воздух', 'Вода', 'Почва', 'Отходы', 'Шум',
        'Радиация', 'Лес', 'Свалки', 'Сточные воды', 'Выбросы',
        'Экологический мониторинг', 'Загрязнение', 'Очистка', 'Рекультивация'
    ]
    
    statuses = ['выполнено', 'в работе', 'новая', 'отложено', 'закрыто']
    
    omsu_list = [
        'Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань',
        'Нижний Новгород', 'Челябинск', 'Самара', 'Омск', 'Ростов-на-Дону',
        'Уфа', 'Красноярск', 'Воронеж', 'Пермь', 'Волгоград',
        'Краснодар', 'Саратов', 'Тюмень', 'Тольятти', 'Ижевск',
        'Барнаул', 'Ульяновск', 'Иркутск', 'Хабаровск', 'Ярославль',
        'Владивосток', 'Махачкала', 'Томск', 'Оренбург', 'Кемерово',
        'Новокузнецк', 'Рязань', 'Астрахань', 'Пенза', 'Липецк',
        'Тула', 'Киров', 'Чебоксары', 'Калининград', 'Брянск',
        'Курск', 'Иваново', 'Магнитогорск', 'Тверь', 'Ставрополь',
        'Белгород', 'Сочи', 'Владимир', 'Архангельск', 'Чита'
    ]
    
    mro_list = [
        'МРО-Центр', 'МРО-Север', 'МРО-Юг', 'МРО-Восток', 'МРО-Запад',
        'МРО-Урал', 'МРО-Сибирь', 'МРО-Дальний', 'МРО-Приволжье', 'МРО-Кавказ'
    ]
    
    # Генерация данных
    np.random.seed(42)
    random.seed(42)
    
    # Даты (последние 2 года)
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 6, 29)
    date_range = (end_date - start_date).days
    
    dates = [start_date + timedelta(days=random.randint(0, date_range)) 
             for _ in range(n_rows)]
    
    # Генерация остальных колонок
    data = {
        'date': dates,
        'status': [random.choice(statuses) for _ in range(n_rows)],
        'category': [random.choice(categories) for _ in range(n_rows)],
        'omsu': [random.choice(omsu_list) for _ in range(n_rows)],
        'mro': [random.choice(mro_list) for _ in range(n_rows)],
        'value': np.random.randint(1, 1000, n_rows),
        'priority': np.random.choice(['Высокий', 'Средний', 'Низкий'], n_rows, p=[0.2, 0.5, 0.3]),
        'department': np.random.choice(['ДЭП', 'Управление', 'Отдел', 'Служба'], n_rows),
        'region': np.random.choice(['ЦФО', 'СЗФО', 'ЮФО', 'СКФО', 'ПФО', 'УФО', 'СФО', 'ДФО'], n_rows)
    }
    
    df = pd.DataFrame(data)
    
    # Добавляем корреляции для реалистичности
    waste_categories = ['Свалки', 'Отходы', 'Сточные воды']
    mask = df['category'].isin(waste_categories)
    df.loc[mask, 'status'] = np.random.choice(
        ['выполнено', 'в работе', 'новая'], 
        size=mask.sum(),
        p=[0.3, 0.4, 0.3]
    )
    
    df.loc[df['value'] > 500, 'priority'] = 'Высокий'
    df.loc[df['value'] < 100, 'priority'] = 'Низкий'
    
    # Добавляем случайные пропуски
    null_mask = np.random.random(n_rows) < 0.02
    df.loc[null_mask, 'department'] = None
    
    null_mask = np.random.random(n_rows) < 0.01
    df.loc[null_mask, 'priority'] = None
    
    # Форматирование дат
    df['date'] = pd.to_datetime(df['date'])
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Сортировка по дате
    df = df.sort_values('date').reset_index(drop=True)
    
    # Добавляем ID
    df.insert(0, 'id', range(1, len(df) + 1))
    
    print(f"✅ Датасет создан: {len(df):,} строк, {len(df.columns)} колонок")
    print(f"📅 Период: {df['date'].min().date()} - {df['date'].max().date()}")
    print(f"📊 Категорий: {df['category'].nunique()}")
    print(f"🏙️ ОМСУ: {df['omsu'].nunique()}")
    print(f"📋 Статусов: {df['status'].unique().tolist()}")
    print(f"📈 Среднее значение: {df['value'].mean():.2f}")
    print(f"📊 Пропусков: {df.isnull().sum().sum()}")
    
    return df


def save_dataset(df, filename='eco_data.xlsx'):
    """Сохраняет датасет в Excel (без xlsxwriter)"""
    print(f"\n💾 Сохранение в {filename}...")
    
    # Используем openpyxl (уже есть в pandas)
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='EcoData', index=False)
    
    file_size = os.path.getsize(filename) / 1024 / 1024
    print(f"✅ Файл сохранён: {filename} ({file_size:.2f} МБ)")
    print(f"📊 Строк: {len(df):,}, Колонок: {len(df.columns)}")


def generate_sample_dataset():
    """Генерирует тестовые датасеты разных размеров"""
    
    print("="*60)
    print("📊 ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАТАСЕТОВ")
    print("="*60)
    
    # 1. Большой датасет (50 000 строк)
    df_large = generate_eco_dataset(50000)
    save_dataset(df_large, 'eco_data_50k.xlsx')
    
    # 2. Средний датасет (10 000 строк)
    df_medium = generate_eco_dataset(10000)
    save_dataset(df_medium, 'eco_data_10k.xlsx')
    
    # 3. Маленький датасет (1 000 строк) для быстрого тестирования
    df_small = generate_eco_dataset(1000)
    save_dataset(df_small, 'eco_data_test.xlsx')
    
    print("\n" + "="*60)
    print("📊 ВСЕ ДАТАСЕТЫ СОЗДАНЫ:")
    print("  📄 eco_data_test.xlsx  - 1 000 строк (для тестов)")
    print("  📄 eco_data_10k.xlsx   - 10 000 строк (рекомендуемый)")
    print("  📄 eco_data_50k.xlsx   - 50 000 строк (для теста производительности)")
    print("="*60)


if __name__ == "__main__":
    generate_sample_dataset()
    print("\n✅ Готово! Файлы сохранены в текущей папке.")