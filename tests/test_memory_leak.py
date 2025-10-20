"""
Основные тесты для обнаружения утечек памяти
Тесты длятся 10-15 минут для реалистичного обнаружения
"""
import pytest
import allure
import time
from utils.memory_monitor import MemoryMonitor
from utils.load_generator import LoadGenerator
from utils.report_builder import ReportBuilder


@allure.feature('Memory Leak Detection')
@allure.story('Long Running Tests')
class TestMemoryLeakDetection:
    
    @allure.title('Обнаружение утечки памяти - Приложение С утечкой (10 минут)')
    @allure.description('''
    Тест запускает приложение с утечками памяти на 10 минут.
    Генерирует нагрузку на все endpoints с утечками:
    - /api/cache - утечка кеша
    - /api/database - незакрытые DB соединения
    - /api/file - файловые дескрипторы
    - /api/redis - Redis connection pool
    
    Ожидается: Постоянный рост памяти > 50 MB
    ''')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.leak
    @pytest.mark.timeout(720)  # 12 минут таймаут (10 мин тест + запас)
    def test_app_with_leak_10min(self, app_with_leak_container):
        """
        Тест приложения С утечкой - 10 минут
        """
        container = app_with_leak_container
        duration = 600  # 10 минут
        base_url = "http://localhost:5000"
        
        # Инициализация
        monitor = MemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("Начало теста - запись начального состояния"):
            initial_memory = monitor.get_current_memory()
            allure.attach(
                f"RSS: {initial_memory['rss_mb']:.2f} MB\n"
                f"VMS: {initial_memory['vms_mb']:.2f} MB",
                name="Начальная память",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step(f"Генерация нагрузки в течение {duration} секунд"):
            memory_data = []
            start_time = time.time()
            
            # Запускаем генератор нагрузки в отдельном потоке
            load_gen.start(
                endpoints=['/api/cache', '/api/database', '/api/file', '/api/stress'],
                rps=5,  # 5 запросов в секунду
                duration=duration
            )
            
            # Мониторим память каждые 5 секунд
            while time.time() - start_time < duration:
                mem = monitor.get_current_memory()
                elapsed = time.time() - start_time
                
                memory_data.append({
                    'time': elapsed,
                    'rss_mb': mem['rss_mb'],
                    'vms_mb': mem['vms_mb'],
                    'percent': mem['percent']
                })
                
                # Логируем каждую минуту
                if int(elapsed) % 60 == 0:
                    print(f"⏱️  {int(elapsed/60)} мин: RSS={mem['rss_mb']:.2f} MB, "
                          f"VMS={mem['vms_mb']:.2f} MB, CPU={mem['percent']:.1f}%")
                
                time.sleep(5)
            
            load_gen.stop()
        
        with allure.step("Анализ результатов"):
            final_memory = monitor.get_current_memory()
            memory_growth = final_memory['rss_mb'] - initial_memory['rss_mb']
            
            # Строим графики
            chart_path = report.create_memory_chart(
                memory_data,
                title="Потребление памяти - App WITH Leak (10 min)",
                filename="memory_with_leak_10min.png"
            )
            allure.attach.file(chart_path, name="График памяти", attachment_type=allure.attachment_type.PNG)
            
            # Анализ тренда
            trend_analysis = report.analyze_trend(memory_data)
            allure.attach(
                f"Рост памяти: {memory_growth:.2f} MB\n"
                f"Тренд: {trend_analysis['trend']}\n"
                f"Скорость роста: {trend_analysis['growth_rate']:.2f} MB/мин\n"
                f"Коэффициент роста: {trend_analysis['growth_coefficient']:.4f}",
                name="Анализ тренда",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Статистика нагрузки
            load_stats = load_gen.get_statistics()
            allure.attach(
                f"Всего запросов: {load_stats['total_requests']}\n"
                f"Успешных: {load_stats['successful']}\n"
                f"Ошибок: {load_stats['errors']}\n"
                f"Среднее время ответа: {load_stats['avg_response_time']:.3f} сек",
                name="Статистика нагрузки",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Вердикт: Обнаружена ли утечка?"):
            # Критерии утечки:
            # 1. Рост памяти > 50 MB
            # 2. Постоянный восходящий тренд
            # 3. Скорость роста > 3 MB/мин
            
            is_leak = (
                memory_growth > 50 and
                trend_analysis['trend'] == 'increasing' and
                trend_analysis['growth_rate'] > 3.0
            )
            
            verdict = "🔴 УТЕЧКА ОБНАРУЖЕНА" if is_leak else "🟢 Утечка не обнаружена"
            
            allure.attach(
                f"{verdict}\n\n"
                f"Критерии:\n"
                f"✓ Рост > 50 MB: {'ДА' if memory_growth > 50 else 'НЕТ'} ({memory_growth:.2f} MB)\n"
                f"✓ Тренд растущий: {'ДА' if trend_analysis['trend'] == 'increasing' else 'НЕТ'}\n"
                f"✓ Скорость > 3 MB/мин: {'ДА' if trend_analysis['growth_rate'] > 3.0 else 'НЕТ'} "
                f"({trend_analysis['growth_rate']:.2f} MB/мин)",
                name="🎯 ВЕРДИКТ",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Ожидаем найти утечку
            assert is_leak, f"Ожидалась утечка памяти, но рост всего {memory_growth:.2f} MB"
    
    
    @allure.title('Обнаружение утечки памяти - Приложение БЕЗ утечки (10 минут)')
    @allure.description('''
    Тест запускает приложение БЕЗ утечек памяти на 10 минут.
    Генерирует аналогичную нагрузку на endpoints:
    - /api/cache - cache с TTL
    - /api/database - connection pool
    - /api/file - context managers
    - /api/redis - переиспользуемый клиент
    
    Ожидается: Стабильное потребление памяти (< 30 MB роста)
    ''')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.leak
    @pytest.mark.timeout(720)
    def test_app_without_leak_10min(self, app_without_leak_container):
        """
        Тест приложения БЕЗ утечки - 10 минут
        """
        container = app_without_leak_container
        duration = 600  # 10 минут
        base_url = "http://localhost:5001"
        
        monitor = MemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("Начало теста - запись начального состояния"):
            initial_memory = monitor.get_current_memory()
            allure.attach(
                f"RSS: {initial_memory['rss_mb']:.2f} MB\n"
                f"VMS: {initial_memory['vms_mb']:.2f} MB",
                name="Начальная память",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step(f"Генерация нагрузки в течение {duration} секунд"):
            memory_data = []
            start_time = time.time()
            
            load_gen.start(
                endpoints=['/api/cache', '/api/database', '/api/file', '/api/stress'],
                rps=5,
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
                    print(f"⏱️  {int(elapsed/60)} мин: RSS={mem['rss_mb']:.2f} MB, "
                          f"VMS={mem['vms_mb']:.2f} MB, CPU={mem['percent']:.1f}%")
                
                time.sleep(5)
            
            load_gen.stop()
        
        with allure.step("Анализ результатов"):
            final_memory = monitor.get_current_memory()
            memory_growth = final_memory['rss_mb'] - initial_memory['rss_mb']
            
            chart_path = report.create_memory_chart(
                memory_data,
                title="Потребление памяти - App WITHOUT Leak (10 min)",
                filename="memory_without_leak_10min.png"
            )
            allure.attach.file(chart_path, name="График памяти", attachment_type=allure.attachment_type.PNG)
            
            trend_analysis = report.analyze_trend(memory_data)
            allure.attach(
                f"Рост памяти: {memory_growth:.2f} MB\n"
                f"Тренд: {trend_analysis['trend']}\n"
                f"Скорость роста: {trend_analysis['growth_rate']:.2f} MB/мин\n"
                f"Коэффициент роста: {trend_analysis['growth_coefficient']:.4f}",
                name="Анализ тренда",
                attachment_type=allure.attachment_type.TEXT
            )
            
            load_stats = load_gen.get_statistics()
            allure.attach(
                f"Всего запросов: {load_stats['total_requests']}\n"
                f"Успешных: {load_stats['successful']}\n"
                f"Ошибок: {load_stats['errors']}\n"
                f"Среднее время ответа: {load_stats['avg_response_time']:.3f} сек",
                name="Статистика нагрузки",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Вердикт: Обнаружена ли утечка?"):
            is_leak = (
                memory_growth > 50 and
                trend_analysis['trend'] == 'increasing' and
                trend_analysis['growth_rate'] > 3.0
            )
            
            verdict = "🔴 УТЕЧКА ОБНАРУЖЕНА" if is_leak else "🟢 Утечка не обнаружена"
            
            allure.attach(
                f"{verdict}\n\n"
                f"Критерии:\n"
                f"✓ Рост > 50 MB: {'ДА' if memory_growth > 50 else 'НЕТ'} ({memory_growth:.2f} MB)\n"
                f"✓ Тренд растущий: {'ДА' if trend_analysis['trend'] == 'increasing' else 'НЕТ'}\n"
                f"✓ Скорость > 3 MB/мин: {'ДА' if trend_analysis['growth_rate'] > 3.0 else 'НЕТ'} "
                f"({trend_analysis['growth_rate']:.2f} MB/мин)",
                name="🎯 ВЕРДИКТ",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # НЕ ожидаем найти утечку
            assert not is_leak, f"Неожиданная утечка памяти: рост {memory_growth:.2f} MB"
    
    
    @allure.title('Сравнительный тест - 15 минут')
    @allure.description('Запускает оба приложения одновременно для сравнения')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.slow
    @pytest.mark.timeout(1080)  # 18 минут
    def test_comparative_15min(self, app_with_leak_container, app_without_leak_container):
        """
        Сравнительный тест обоих приложений - 15 минут
        """
        duration = 900  # 15 минут
        
        # Мониторы
        monitor_leak = MemoryMonitor(app_with_leak_container)
        monitor_no_leak = MemoryMonitor(app_without_leak_container)
        
        # Генераторы нагрузки
        load_leak = LoadGenerator("http://localhost:5000")
        load_no_leak = LoadGenerator("http://localhost:5001")
        
        report = ReportBuilder()
        
        with allure.step("Запуск параллельного мониторинга"):
            data_leak = []
            data_no_leak = []
            
            # Запускаем нагрузку на оба
            load_leak.start(
                endpoints=['/api/cache', '/api/database', '/api/file', '/api/stress'],
                rps=5,
                duration=duration
            )
            load_no_leak.start(
                endpoints=['/api/cache', '/api/database', '/api/file', '/api/stress'],
                rps=5,
                duration=duration
            )
            
            start_time = time.time()
            
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                
                mem_leak = monitor_leak.get_current_memory()
                mem_no_leak = monitor_no_leak.get_current_memory()
                
                data_leak.append({
                    'time': elapsed,
                    'rss_mb': mem_leak['rss_mb'],
                    'vms_mb': mem_leak['vms_mb']
                })
                
                data_no_leak.append({
                    'time': elapsed,
                    'rss_mb': mem_no_leak['rss_mb'],
                    'vms_mb': mem_no_leak['vms_mb']
                })
                
                if int(elapsed) % 60 == 0:
                    print(f"⏱️  {int(elapsed/60)} мин:")
                    print(f"   WITH leak: RSS={mem_leak['rss_mb']:.2f} MB")
                    print(f"   WITHOUT leak: RSS={mem_no_leak['rss_mb']:.2f} MB")
                
                time.sleep(5)
            
            load_leak.stop()
            load_no_leak.stop()
        
        with allure.step("Сравнительный анализ"):
            # Создаем сравнительный график
            chart_path = report.create_comparison_chart(
                data_leak,
                data_no_leak,
                title="Сравнение потребления памяти (15 min)",
                filename="memory_comparison_15min.png"
            )
            allure.attach.file(chart_path, name="Сравнительный график", attachment_type=allure.attachment_type.PNG)
            
            # Анализ трендов
            trend_leak = report.analyze_trend(data_leak)
            trend_no_leak = report.analyze_trend(data_no_leak)
            
            growth_leak = data_leak[-1]['rss_mb'] - data_leak[0]['rss_mb']
            growth_no_leak = data_no_leak[-1]['rss_mb'] - data_no_leak[0]['rss_mb']
            
            allure.attach(
                f"📊 СРАВНИТЕЛЬНЫЙ ОТЧЕТ\n\n"
                f"С УТЕЧКОЙ:\n"
                f"  Рост памяти: {growth_leak:.2f} MB\n"
                f"  Скорость: {trend_leak['growth_rate']:.2f} MB/мин\n"
                f"  Тренд: {trend_leak['trend']}\n\n"
                f"БЕЗ УТЕЧКИ:\n"
                f"  Рост памяти: {growth_no_leak:.2f} MB\n"
                f"  Скорость: {trend_no_leak['growth_rate']:.2f} MB/мин\n"
                f"  Тренд: {trend_no_leak['trend']}\n\n"
                f"РАЗНИЦА:\n"
                f"  Рост памяти: {growth_leak - growth_no_leak:.2f} MB\n"
                f"  Соотношение: {growth_leak / max(growth_no_leak, 1):.2f}x",
                name="📈 Сравнительный анализ",
                attachment_type=allure.attachment_type.TEXT
            )
