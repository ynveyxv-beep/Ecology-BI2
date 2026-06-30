# test_eco_functions.py - Тест функций Славика
import pandas as pd
from eco_modules import (
    get_kpi, get_by_category, get_by_omsu, get_by_mro,
    get_time_series, get_trash_analysis
)

# Загружаем данные
df = pd.read_excel('eco_data_test.xlsx', engine='openpyxl')

# Нормализуем как в приложении
df.columns = [str(col).strip().lower() for col in df.columns]
if 'date' in df.columns:
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
if 'status' in df.columns:
    df['status'] = df['status'].astype(str).str.lower().str.strip()
    df['status'] = df['status'].apply(
        lambda x: 'выполнено' if any(w in x for w in ['выполн', 'done', 'closed', 'закрыт', 'complete'])
        else 'в работе' if any(w in x for w in ['работ', 'progress', 'open', 'ожида'])
        else x
    )

print(f"📊 Данных: {len(df)} строк")
print(f"📋 Колонки: {df.columns.tolist()}")
print(f"📊 Статусы: {df['status'].unique().tolist()}")
print(f"📊 Категории: {df['category'].unique().tolist()[:5]}")
print(f"📊 ОМСУ: {df['omsu'].unique().tolist()[:5]}")
print("="*60)

# Тестируем каждую функцию
try:
    print("1. get_kpi()...")
    kpi = get_kpi(df)
    print(f"   ✅ KPI: {kpi}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

try:
    print("2. get_time_series()...")
    ts = get_time_series(df, freq='D')
    print(f"   ✅ Временной ряд: {len(ts)} строк")
    print(f"   {ts.head()}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

try:
    print("3. get_by_category()...")
    cat = get_by_category(df)
    print(f"   ✅ Категории: {len(cat)} строк")
    print(f"   {cat.head()}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

try:
    print("4. get_by_omsu()...")
    omsu = get_by_omsu(df)
    print(f"   ✅ ОМСУ: {len(omsu)} строк")
    print(f"   {omsu.head()}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

try:
    print("5. get_by_mro()...")
    mro = get_by_mro(df)
    print(f"   ✅ МРО: {len(mro)} строк")
    print(f"   {mro.head()}")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")

try:
    print("6. get_trash_analysis()...")
    top_count, top_backlog = get_trash_analysis(df)
    print(f"   ✅ Мусор (count): {len(top_count)} строк")
    print(f"   ✅ Мусор (backlog): {len(top_backlog)} строк")
except Exception as e:
    print(f"   ❌ Ошибка: {e}")