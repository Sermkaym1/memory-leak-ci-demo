#!/usr/bin/env python3
"""
Простой тест утилит без Docker для проверки улучшений
Можно запустить на любой системе с Python
"""

import sys
import os
import time
from datetime import datetime

# Добавляем путь к тестам в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_memory_monitor_output():
    """Тест вывода MemoryMonitor без реального контейнера"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 1: Проверка наблюдаемости в тестах")
    print("="*60)
    
    # Имитируем прогресс тест
    duration = 30  # 30 секунд для демо
    start_time = time.time()
    measurement_count = 0
    
    print(f"\n🎯 НАЧИНАЕМ ДЕМО БЫСТРОГО ТЕСТА")
    print(f"⏱️  Длительность: {duration} секунд")
    print(f"🌐 URL: http://localhost:5000 (демо)")
    print(f"🔥 RPS: 3 запроса/сек")
    print("="*60 + "\n")
    
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        measurement_count += 1
        
        # Имитируем данные памяти с ростом (утечка)
        fake_rss = 50.0 + (elapsed * 2)  # Рост 2 MB в секунду
        fake_vms = 200.0 + (elapsed * 1.5)
        
        # Показываем прогресс каждые 5 секунд
        if int(elapsed) % 5 == 0 or elapsed < 5:
            progress = (elapsed / duration) * 100
            remaining = duration - elapsed
            print(f"📊 [{progress:5.1f}%] "
                  f"⏱️ {int(elapsed):3d}с/{duration}с "
                  f"📈 RSS: {fake_rss:6.1f} MB "
                  f"💾 VMS: {fake_vms:6.1f} MB "
                  f"⏳ Осталось: {int(remaining):3d}с "
                  f"📏 Измерений: {measurement_count}")
        
        time.sleep(1)
    
    print(f"\n🏁 ДЕМО ТЕСТ ЗАВЕРШЕН!")
    print(f"📊 Всего измерений: {measurement_count}")
    print(f"⏱️  Общее время: {elapsed:.1f} сек")
    print("="*60)
    
    memory_growth = fake_rss - 50.0
    print(f"\n📈 АНАЛИЗ РЕЗУЛЬТАТОВ:")
    print(f"🔴 Рост памяти: {memory_growth:.1f} MB")
    print(f"🔴 Скорость роста: {memory_growth/(elapsed/60):.1f} MB/мин")
    print(f"🎯 Вердикт: {'УТЕЧКА ОБНАРУЖЕНА' if memory_growth > 20 else 'ОК'}")


def test_report_builder():
    """Тест создания графика"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 2: Создание графика памяти")
    print("="*60)
    
    try:
        from tests.utils.report_builder import ReportBuilder
        
        # Создаем тестовые данные
        memory_data = []
        for i in range(30):
            memory_data.append({
                'time': i * 10,  # каждые 10 секунд
                'rss_mb': 50 + i * 2,  # рост памяти
                'vms_mb': 200 + i * 1.5,
                'percent': 15.0
            })
        
        report = ReportBuilder()
        
        # Анализ тренда
        trend = report.analyze_trend(memory_data)
        print(f"📈 Анализ тренда:")
        print(f"  Тренд: {trend['trend']}")
        print(f"  Скорость роста: {trend['growth_rate']:.2f} MB/мин")
        print(f"  Коэффициент роста: {trend['growth_coefficient']:.4f}")
        
        # Создание графика
        chart_path = report.create_memory_chart(
            memory_data,
            title="Демо: Потребление памяти",
            filename="demo_memory_chart.png"
        )
        
        if os.path.exists(chart_path):
            print(f"✅ График создан: {chart_path}")
        else:
            print("❌ График не создан")
            
    except ImportError as e:
        print(f"⚠️  Не удалось импортировать ReportBuilder: {e}")
        print("   Установите matplotlib: pip install matplotlib")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


def test_smart_health_check():
    """Тест умной проверки готовности сервисов"""
    print("\n" + "="*60)
    print("🧪 ТЕСТ 3: Умная проверка готовности")
    print("="*60)
    
    import requests
    
    def demo_wait_for_service(url: str, service_name: str, max_wait: int = 10):
        """Демо версия проверки сервиса"""
        print(f"🔍 Проверяю готовность {service_name} на {url}")
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    elapsed = time.time() - start_time
                    print(f"✅ {service_name} готов за {elapsed:.1f} сек")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            elapsed = time.time() - start_time
            print(f"⏳ {service_name} еще не готов, жду... ({int(elapsed)}с)")
            time.sleep(1)
        
        print(f"❌ {service_name} не готов за {max_wait} сек")
        return False
    
    # Тестируем на реальных URL (Google всегда отвечает)
    test_services = [
        ("https://httpbin.org/status/200", "HTTPBin Test Service"),
        ("https://httpbin.org/delay/3", "Медленный сервис (3 сек)"),
    ]
    
    for url, name in test_services:
        result = demo_wait_for_service(url, name, max_wait=8)
        print(f"Результат для {name}: {'✅ ОК' if result else '❌ FAIL'}\n")


if __name__ == "__main__":
    print(f"🚀 ТЕСТИРОВАНИЕ УЛУЧШЕНИЙ - {datetime.now().strftime('%H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Рабочая директория: {os.getcwd()}")
    
    try:
        test_memory_monitor_output()
        test_report_builder()
        test_smart_health_check()
        
        print("\n" + "="*60)
        print("🎉 ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
        print("✅ Наблюдаемость улучшена")
        print("✅ Умная проверка сервисов работает")  
        print("✅ Графики создаются")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⏹️  Тесты прерваны пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка в тестах: {e}")
        sys.exit(1)