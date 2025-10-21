#!/usr/bin/env python3
"""
Отладка проблем с графиками
"""

from tests.utils.enhanced_monitor import SystemMetrics
from tests.utils.report_builder import ReportBuilder
import time

# Создаем тестовые данные как в реальном тесте
test_data = []

# Симулируем данные за 1 минуту с интервалом 10 сек (6 точек)
for i in range(6):
    elapsed = i * 10  # 0, 10, 20, 30, 40, 50 секунд
    
    # Симулируем рост памяти с утечкой
    baseline_rss = 27.7
    growth = (elapsed / 60) * 5.9  # Рост 5.9 MB за минуту
    rss_mb = baseline_rss + growth
    
    baseline_vms = 33.6
    vms_growth = (elapsed / 60) * 1.0  # Небольшой рост VMS
    vms_mb = baseline_vms + vms_growth
    
    test_data.append({
        'time': elapsed,
        'rss_mb': rss_mb,
        'vms_mb': vms_mb,
        'percent': 5.2 + growth * 0.1
    })

print("Тестовые данные:")
for i, data in enumerate(test_data):
    print(f"Точка {i}: time={data['time']}с, RSS={data['rss_mb']:.1f}MB, VMS={data['vms_mb']:.1f}MB")

print(f"\nВсего точек: {len(test_data)}")
print(f"Начальная RSS: {test_data[0]['rss_mb']:.1f} MB")
print(f"Конечная RSS: {test_data[-1]['rss_mb']:.1f} MB")
print(f"Рост RSS: {test_data[-1]['rss_mb'] - test_data[0]['rss_mb']:.1f} MB")

# Проверяем типы данных
print(f"\nТипы данных:")
print(f"time: {type(test_data[0]['time'])}")
print(f"rss_mb: {type(test_data[0]['rss_mb'])}")
print(f"vms_mb: {type(test_data[0]['vms_mb'])}")

# Проверяем есть ли нулевые или отрицательные значения
print(f"\nПроверка значений:")
for i, data in enumerate(test_data):
    if data['rss_mb'] <= 0:
        print(f"⚠️  ПРОБЛЕМА: RSS <= 0 в точке {i}: {data['rss_mb']}")
    if data['vms_mb'] <= 0:
        print(f"⚠️  ПРОБЛЕМА: VMS <= 0 в точке {i}: {data['vms_mb']}")
    if data['time'] < 0:
        print(f"⚠️  ПРОБЛЕМА: Time < 0 в точке {i}: {data['time']}")

# Создаем график
print(f"\nСоздаем график...")
try:
    report = ReportBuilder()
    chart_path = report.create_memory_chart(
        test_data,
        title="Debug Test - App WITH Leak (1 min)",
        filename="debug_memory_chart.png"
    )
    print(f"✅ График создан: {chart_path}")
except Exception as e:
    print(f"❌ Ошибка создания графика: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()