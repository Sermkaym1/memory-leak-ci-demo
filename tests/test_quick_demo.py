"""
Быстрые тесты для демонстрации (5 минут)
Используйте для проверки что все работает
"""
import pytest
import allure
import time
from .utils.enhanced_monitor import EnhancedMemoryMonitor
from .utils.load_generator import LoadGenerator
from .utils.report_builder import ReportBuilder


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
        duration = 60  # Сократим до 1 минуты для быстрого теста
        base_url = "http://localhost:5000"
        
        print(f"\n🔍 Проверка контейнера: {container.name}")
        print(f"📊 Статус: {container.status}")
        
        # Простая проверка доступности
        import requests
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            print(f"✅ Сервис отвечает: {response.status_code}")
        except Exception as e:
            print(f"❌ Сервис недоступен: {e}")
            pytest.skip("Сервис недоступен")
        
        monitor = EnhancedMemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("Начало быстрого теста"):
            initial_memory = monitor.get_detailed_metrics()
            allure.attach(
                f"RSS: {initial_memory.rss_mb:.2f} MB\n"
                f"VMS: {initial_memory.vms_mb:.2f} MB\n"
                f"CPU: {initial_memory.cpu_percent:.1f}%\n"
                f"Connections: {initial_memory.network_connections}",
                name="Начальная память",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step(f"🚀 ГЕНЕРАЦИЯ НАГРУЗКИ {duration} секунд"):
            memory_data = []
            start_time = time.time()
            
            print(f"\n{'='*60}")
            print(f"🎯 НАЧИНАЕМ БЫСТРЫЙ ТЕСТ С УТЕЧКОЙ")
            print(f"⏱️  Длительность: {duration} секунд ({duration//60} мин {duration%60} сек)")
            print(f"🌐 URL: {base_url}")
            print(f"🔥 RPS: 1 запроса/сек")
            print(f"{'='*60}\n")
            
            load_gen.start(
                endpoints=['/api/stress'],  # Только один endpoint для упрощения
                rps=1,  # Минимальная нагрузка
                duration=duration
            )
            
            measurement_count = 0
            while time.time() - start_time < duration:
                mem = monitor.get_detailed_metrics()
                elapsed = time.time() - start_time
                measurement_count += 1
                
                memory_data.append({
                    'time': elapsed,
                    'rss_mb': mem.rss_mb,
                    'vms_mb': mem.vms_mb,
                    'percent': mem.memory_percent
                })
                
                # УЛУЧШЕННАЯ НАБЛЮДАЕМОСТЬ - каждые 30 сек показываем прогресс
                if int(elapsed) % 30 == 0 or elapsed < 30:
                    progress = (elapsed / duration) * 100
                    remaining = duration - elapsed
                    print(f"📊 [{progress:5.1f}%] "
                          f"⏱️ {int(elapsed):3d}с/{duration}с "
                          f"📈 RSS: {mem.rss_mb:6.1f} MB "
                          f"💾 VMS: {mem.vms_mb:6.1f} MB "
                          f"⏳ Осталось: {int(remaining):3d}с "
                          f"📏 Измерений: {measurement_count}")
                
                time.sleep(10)  # Собираем данные каждые 10 сек
            
            load_gen.stop()
            
            print(f"\n🏁 ТЕСТ ЗАВЕРШЕН!")
            print(f"📊 Всего измерений: {len(memory_data)}")
            print(f"⏱️  Общее время: {elapsed:.1f} сек")
            print("="*60)
    
        with allure.step("Анализ"):
            final_memory = monitor.get_detailed_metrics()
            memory_growth = final_memory.rss_mb - initial_memory.rss_mb
            
            chart_path = report.create_memory_chart(
                memory_data,
                title="Quick Test - App WITH Leak (1 min)",
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
    
    
    @allure.title('Быстрый тест - Приложение БЕЗ утечки (1 минута)')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.timeout(180)
    def test_quick_without_leak(self, app_without_leak_container):
        """
        Быстрый тест приложения БЕЗ утечки - 1 минута
        """
        container = app_without_leak_container
        duration = 60  # Сократим до 1 минуты
        base_url = "http://localhost:5001"
        
        print(f"\n🔍 Проверка контейнера: {container.name}")
        print(f"📊 Статус: {container.status}")
        
        # Простая проверка доступности
        import requests
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            print(f"✅ Сервис отвечает: {response.status_code}")
        except Exception as e:
            print(f"❌ Сервис недоступен: {e}")
            pytest.skip("Сервис недоступен")
        
        monitor = EnhancedMemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("Начало быстрого теста"):
            initial_memory = monitor.get_detailed_metrics()
        
        with allure.step(f"🚀 ГЕНЕРАЦИЯ НАГРУЗКИ {duration} секунд"):
            memory_data = []
            start_time = time.time()
            
            print(f"\n{'='*60}")
            print(f"🎯 НАЧИНАЕМ БЫСТРЫЙ ТЕСТ БЕЗ УТЕЧКИ")
            print(f"⏱️  Длительность: {duration} секунд ({duration//60} мин {duration%60} сек)")
            print(f"🌐 URL: {base_url}")
            print(f"🔥 RPS: 3 запроса/сек")
            print(f"{'='*60}\n")
            
            load_gen.start(
                endpoints=['/api/cache', '/api/stress'],
                rps=3,
                duration=duration
            )
            
            measurement_count = 0
            while time.time() - start_time < duration:
                mem = monitor.get_detailed_metrics()
                elapsed = time.time() - start_time
                measurement_count += 1
                
                memory_data.append({
                    'time': elapsed,
                    'rss_mb': mem.rss_mb,
                    'vms_mb': mem.vms_mb,
                    'percent': mem.memory_percent
                })
                
                # УЛУЧШЕННАЯ НАБЛЮДАЕМОСТЬ - каждые 30 сек показываем прогресс
                if int(elapsed) % 30 == 0 or elapsed < 30:
                    progress = (elapsed / duration) * 100
                    remaining = duration - elapsed
                    print(f"📊 [{progress:5.1f}%] "
                          f"⏱️ {int(elapsed):3d}с/{duration}с "
                          f"📈 RSS: {mem.rss_mb:6.1f} MB "
                          f"💾 VMS: {mem.vms_mb:6.1f} MB "
                          f"⏳ Осталось: {int(remaining):3d}с "
                          f"📏 Измерений: {measurement_count}")
                
                time.sleep(10)
            
            load_gen.stop()
            
            print(f"\n🏁 ТЕСТ ЗАВЕРШЕН!")
            print(f"📊 Всего измерений: {len(memory_data)}")
            print(f"⏱️  Общее время: {elapsed:.1f} сек")
            print("="*60)
        
        with allure.step("Анализ"):
            final_memory = monitor.get_detailed_metrics()
            memory_growth = final_memory.rss_mb - initial_memory.rss_mb
            
            chart_path = report.create_memory_chart(
                memory_data,
                title="Quick Test - App WITHOUT Leak (1 min)",
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
