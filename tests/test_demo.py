"""
Демо-версия тестов на обнаружение утечек памяти
Быстрый запуск (30 секунд) для показа CI/CD
"""
import pytest
import time
import allure
from tests.utils.enhanced_monitor import EnhancedMemoryMonitor
from tests.utils.load_generator import LoadGenerator  
from tests.utils.report_builder import ReportBuilder


@allure.epic("Demo Memory Leak Detection")
@allure.feature("Quick Demo Tests")
class TestDemoMemoryLeak:
    """Демо-тесты для быстрого показа CI/CD"""
    
    @allure.story("App WITH Memory Leak - 30sec Demo")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_demo_app_with_leak_30sec(self, app_with_leak_container):
        """🚨 Демо: Приложение С утечкой памяти (30 сек)"""
        
        container = app_with_leak_container
        duration = 30  # Всего 30 секунд для демо
        base_url = "http://localhost:5000"
        
        # Инициализация
        monitor = EnhancedMemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("🎯 ДЕМО: Начальное состояние"):
            initial_memory = monitor.get_detailed_metrics()
            allure.attach(
                f"🏁 Начальная память:\n"
                f"RSS: {initial_memory.rss_mb:.1f} MB\n"
                f"VMS: {initial_memory.vms_mb:.1f} MB",
                name="Начальная память",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step(f"⚡ ДЕМО: Генерация нагрузки ({duration}с)"):
            memory_data = []
            start_time = time.time()
            
            # Запускаем генератор нагрузки
            load_gen.start(
                endpoints=['/api/stress', '/api/cache'],  # Только основные endpoints
                rps=10,  # Увеличенная нагрузка для быстрого эффекта
                duration=duration
            )
            
            # Собираем данные каждые 5 секунд (6 точек за 30 сек)
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                mem = monitor.get_detailed_metrics()
                
                memory_data.append({
                    'time': elapsed,
                    'rss_mb': mem.rss_mb,
                    'vms_mb': mem.vms_mb,
                    'percent': mem.memory_percent
                })
                
                # Показываем прогресс для демо
                progress = (elapsed / duration) * 100
                print(f"🎯 DEMO [{progress:5.1f}%] "
                      f"⏱️ {int(elapsed)}с/{duration}с "
                      f"📈 RSS: {mem.rss_mb:6.1f} MB")
                
                time.sleep(5)  # Интервал сбора данных
            
            load_gen.stop()
    
        with allure.step("📊 ДЕМО: Анализ результатов"):
            final_memory = monitor.get_detailed_metrics()
            memory_growth = final_memory.rss_mb - initial_memory.rss_mb
            
            # Создаем график
            chart_path = report.create_memory_chart(
                memory_data,
                title="🚨 DEMO: Memory Leak Detection (30 sec)",
                filename="demo_memory_leak_30sec.png"
            )
            
            if chart_path:
                allure.attach.file(chart_path, name="📈 Demo График", attachment_type=allure.attachment_type.PNG)
            
            # Результаты анализа
            allure.attach(
                f"📊 ДЕМО РЕЗУЛЬТАТЫ:\n"
                f"🏁 Начальная память: {initial_memory.rss_mb:.1f} MB\n"
                f"🏁 Конечная память: {final_memory.rss_mb:.1f} MB\n" 
                f"📈 Рост памяти: +{memory_growth:.1f} MB\n"
                f"⏱️ Время теста: {duration}с\n"
                f"📏 Точек измерений: {len(memory_data)}",
                name="📊 Анализ",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Вердикт для демо
            if memory_growth > 2.0:  # Пороговое значение для демо
                verdict = "🚨 УТЕЧКА ПАМЯТИ ОБНАРУЖЕНА! ⚠️"
                status = "КРИТИЧНО"
            elif memory_growth > 1.0:
                verdict = "⚠️ Подозрение на утечку памяти"
                status = "ВНИМАНИЕ" 
            else:
                verdict = "✅ Утечка памяти НЕ обнаружена"
                status = "ОК"
                
            allure.attach(
                f"🎯 ВЕРДИКТ ДЕМО: {verdict}\n"
                f"📊 Статус: {status}\n"
                f"📈 Рост: +{memory_growth:.1f} MB за {duration}с",
                name="🏁 Итоговый вердикт",
                attachment_type=allure.attachment_type.TEXT
            )
            
            print(f"\n🎯 DEMO RESULTS:")
            print(f"📊 Memory Growth: +{memory_growth:.1f} MB")
            print(f"🏁 Verdict: {verdict}")
            print("="*60)

    @allure.story("App WITHOUT Memory Leak - 30sec Demo")  
    @allure.severity(allure.severity_level.NORMAL)
    def test_demo_app_without_leak_30sec(self, app_without_leak_container):
        """✅ Демо: Приложение БЕЗ утечки памяти (30 сек)"""
        
        container = app_without_leak_container
        duration = 30
        base_url = "http://localhost:5001"
        
        monitor = EnhancedMemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("🎯 ДЕМО: Начальное состояние (БЕЗ утечки)"):
            initial_memory = monitor.get_detailed_metrics()
            allure.attach(
                f"🏁 Начальная память:\n"
                f"RSS: {initial_memory.rss_mb:.1f} MB\n"
                f"VMS: {initial_memory.vms_mb:.1f} MB",
                name="Начальная память",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step(f"⚡ ДЕМО: Нагрузка на здоровое приложение ({duration}с)"):
            memory_data = []
            start_time = time.time()
            
            load_gen.start(
                endpoints=['/api/stress', '/api/cache'],
                rps=10,
                duration=duration
            )
            
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                mem = monitor.get_detailed_metrics()
                
                memory_data.append({
                    'time': elapsed,
                    'rss_mb': mem.rss_mb,
                    'vms_mb': mem.vms_mb,
                    'percent': mem.memory_percent
                })
                
                progress = (elapsed / duration) * 100
                print(f"✅ HEALTHY [{progress:5.1f}%] "
                      f"⏱️ {int(elapsed)}с/{duration}с "
                      f"📈 RSS: {mem.rss_mb:6.1f} MB")
                
                time.sleep(5)
            
            load_gen.stop()
    
        with allure.step("📊 ДЕМО: Анализ здорового приложения"):
            final_memory = monitor.get_detailed_metrics()
            memory_growth = final_memory.rss_mb - initial_memory.rss_mb
            
            chart_path = report.create_memory_chart(
                memory_data,
                title="✅ DEMO: Healthy App - No Memory Leak (30 sec)",
                filename="demo_healthy_app_30sec.png"
            )
            
            if chart_path:
                allure.attach.file(chart_path, name="📈 Healthy График", attachment_type=allure.attachment_type.PNG)
            
            verdict = "✅ ЗДОРОВОЕ ПРИЛОЖЕНИЕ - утечек нет!" if abs(memory_growth) < 1.0 else "⚠️ Небольшой рост памяти"
            
            allure.attach(
                f"🎯 ДЕМО ВЕРДИКТ: {verdict}\n"
                f"📈 Рост: {memory_growth:+.1f} MB за {duration}с\n"
                f"📊 Статус: {'ОК' if abs(memory_growth) < 1.0 else 'ВНИМАНИЕ'}",
                name="🏁 Здоровое приложение",
                attachment_type=allure.attachment_type.TEXT
            )
            
            print(f"\n✅ HEALTHY APP RESULTS:")
            print(f"📊 Memory Growth: {memory_growth:+.1f} MB")
            print(f"🏁 Verdict: {verdict}")
            print("="*60)