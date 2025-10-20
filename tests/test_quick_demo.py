"""
Быстрые тесты для демонстрации (5 минут)
Используйте для проверки что все работает
"""
import pytest
import allure
import time
from utils.memory_monitor import MemoryMonitor
from utils.load_generator import LoadGenerator
from utils.report_builder import ReportBuilder


@allure.feature('Quick Demo')
@allure.story('5-minute tests')
class TestQuickDemo:
    
    @allure.title('Быстрый тест - Приложение С утечкой (5 минут)')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.timeout(420)  # 7 минут таймаут
    def test_quick_with_leak(self, app_with_leak_container):
        """
        Быстрый тест приложения С утечкой - 5 минут
        """
        container = app_with_leak_container
        duration = 300  # 5 минут
        base_url = "http://localhost:5000"
        
        monitor = MemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("Начало быстрого теста"):
            initial_memory = monitor.get_current_memory()
            allure.attach(
                f"RSS: {initial_memory['rss_mb']:.2f} MB\n"
                f"VMS: {initial_memory['vms_mb']:.2f} MB",
                name="Начальная память",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step(f"Нагрузка {duration} секунд"):
            memory_data = []
            start_time = time.time()
            
            load_gen.start(
                endpoints=['/api/cache', '/api/stress'],
                rps=10,  # Меньше RPS для быстрого теста
                duration=duration
            )
            
            while time.time() - start_time < duration:
                mem = monitor.get_current_memory()
                elapsed = time.time() - start_time
                
                memory_data.append({
                    'time': elapsed,
                    'rss_mb': mem['rss_mb'],
                    'vms_mb': mem['vms_mb'],
                    'percent': mem['percent']
                })
                
                if int(elapsed) % 60 == 0:
                    print(f"⏱️  {int(elapsed/60)} мин: RSS={mem['rss_mb']:.2f} MB")
                
                time.sleep(10)  # Реже собираем данные
            
            load_gen.stop()
        
        with allure.step("Анализ"):
            final_memory = monitor.get_current_memory()
            memory_growth = final_memory['rss_mb'] - initial_memory['rss_mb']
            
            chart_path = report.create_memory_chart(
                memory_data,
                title="Quick Test - App WITH Leak (5 min)",
                filename="quick_with_leak.png"
            )
            allure.attach.file(chart_path, name="График", attachment_type=allure.attachment_type.PNG)
            
            trend_analysis = report.analyze_trend(memory_data)
            
            allure.attach(
                f"Рост памяти: {memory_growth:.2f} MB\n"
                f"Тренд: {trend_analysis['trend']}\n"
                f"Скорость: {trend_analysis['growth_rate']:.2f} MB/мин",
                name="Результат",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Для быстрого теста более мягкие критерии
            is_leak = memory_growth > 20 and trend_analysis['trend'] == 'increasing'
            
            verdict = "🔴 УТЕЧКА" if is_leak else "🟢 ОК"
            allure.attach(verdict, name="Вердикт", attachment_type=allure.attachment_type.TEXT)
    
    
    @allure.title('Быстрый тест - Приложение БЕЗ утечки (5 минут)')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.timeout(420)
    def test_quick_without_leak(self, app_without_leak_container):
        """
        Быстрый тест приложения БЕЗ утечки - 5 минут
        """
        container = app_without_leak_container
        duration = 300
        base_url = "http://localhost:5001"
        
        monitor = MemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("Начало быстрого теста"):
            initial_memory = monitor.get_current_memory()
        
        with allure.step(f"Нагрузка {duration} секунд"):
            memory_data = []
            start_time = time.time()
            
            load_gen.start(
                endpoints=['/api/cache', '/api/stress'],
                rps=10,
                duration=duration
            )
            
            while time.time() - start_time < duration:
                mem = monitor.get_current_memory()
                elapsed = time.time() - start_time
                
                memory_data.append({
                    'time': elapsed,
                    'rss_mb': mem['rss_mb'],
                    'vms_mb': mem['vms_mb'],
                    'percent': mem['percent']
                })
                
                if int(elapsed) % 60 == 0:
                    print(f"⏱️  {int(elapsed/60)} мин: RSS={mem['rss_mb']:.2f} MB")
                
                time.sleep(10)
            
            load_gen.stop()
        
        with allure.step("Анализ"):
            final_memory = monitor.get_current_memory()
            memory_growth = final_memory['rss_mb'] - initial_memory['rss_mb']
            
            chart_path = report.create_memory_chart(
                memory_data,
                title="Quick Test - App WITHOUT Leak (5 min)",
                filename="quick_without_leak.png"
            )
            allure.attach.file(chart_path, name="График", attachment_type=allure.attachment_type.PNG)
            
            trend_analysis = report.analyze_trend(memory_data)
            
            allure.attach(
                f"Рост памяти: {memory_growth:.2f} MB\n"
                f"Тренд: {trend_analysis['trend']}\n"
                f"Скорость: {trend_analysis['growth_rate']:.2f} MB/мин",
                name="Результат",
                attachment_type=allure.attachment_type.TEXT
            )
            
            is_leak = memory_growth > 20 and trend_analysis['trend'] == 'increasing'
            verdict = "🔴 УТЕЧКА" if is_leak else "🟢 ОК"
            allure.attach(verdict, name="Вердикт", attachment_type=allure.attachment_type.TEXT)
