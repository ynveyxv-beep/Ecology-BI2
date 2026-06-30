# test_load.py - тестовая загрузка данных без GUI
import pandas as pd
import traceback
import os

def test_load():
    print("="*60)
    print("🧪 ТЕСТ ЗАГРУЗКИ ДАННЫХ")
    print("="*60)
    
    # Проверяем файлы
    test_files = ['eco_data_test.xlsx', 'eco_data_10k.xlsx', 'eco_data.xlsx']
    
    for filename in test_files:
        print(f"\n📄 Проверка: {filename}")
        
        if not os.path.exists(filename):
            print(f"  ❌ Файл не найден")
            continue
        
        try:
            print(f"  📊 Размер: {os.path.getsize(filename) / 1024:.2f} КБ")
            
            # Читаем файл
            df = pd.read_excel(filename)
            print(f"  ✅ Прочитано: {len(df)} строк, {len(df.columns)} колонок")
            print(f"  📋 Колонки: {df.columns.tolist()}")
            
            # Проверяем даты
            if 'date' in df.columns:
                try:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    valid_dates = df['date'].notna().sum()
                    print(f"  📅 Валидных дат: {valid_dates} из {len(df)}")
                    print(f"  📅 Диапазон: {df['date'].min()} - {df['date'].max()}")
                except Exception as e:
                    print(f"  ❌ Ошибка дат: {e}")
            
            # Проверяем статусы
            if 'status' in df.columns:
                unique = df['status'].unique().tolist()
                print(f"  📊 Статусы: {unique[:5]}...")
            
            print(f"  ✅ Файл {filename} - OK!")
            
        except Exception as e:
            print(f"  ❌ ОШИБКА: {e}")
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("🏁 ТЕСТ ЗАВЕРШЁН")

if __name__ == "__main__":
    test_load()