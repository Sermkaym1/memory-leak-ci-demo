"""
Основные тесты для обнаружения утечек памяти
Тесты длятся 10-15 минут для реалистичного обнаружения
"""
import pytest
import allure
import time
from tests.utils.enhanced_monitor import EnhancedMemoryMonitor
from tests.utils.load_generator import LoadGenerator
from tests.utils.report_builder import ReportBuilder


@allure.feature('Memory Leak Detection')
@allure.story('Long Running Tests')
class TestMemoryLeakDetection:
    
    @allure.title('РћР±РЅР°СЂСѓР¶РµРЅРёРµ СѓС‚РµС‡РєРё РїР°РјСЏС‚Рё - РџСЂРёР»РѕР¶РµРЅРёРµ РЎ СѓС‚РµС‡РєРѕР№ (10 РјРёРЅСѓС‚)')
    @allure.description('''
    РўРµСЃС‚ Р·Р°РїСѓСЃРєР°РµС‚ РїСЂРёР»РѕР¶РµРЅРёРµ СЃ СѓС‚РµС‡РєР°РјРё РїР°РјСЏС‚Рё РЅР° 10 РјРёРЅСѓС‚.
    Р“РµРЅРµСЂРёСЂСѓРµС‚ РЅР°РіСЂСѓР·РєСѓ РЅР° РІСЃРµ endpoints СЃ СѓС‚РµС‡РєР°РјРё:
    - /api/cache - СѓС‚РµС‡РєР° РєРµС€Р°
    - /api/database - РЅРµР·Р°РєСЂС‹С‚С‹Рµ DB СЃРѕРµРґРёРЅРµРЅРёСЏ
    - /api/file - С„Р°Р№Р»РѕРІС‹Рµ РґРµСЃРєСЂРёРїС‚РѕСЂС‹
    - /api/redis - Redis connection pool
    
    РћР¶РёРґР°РµС‚СЃСЏ: РџРѕСЃС‚РѕСЏРЅРЅС‹Р№ СЂРѕСЃС‚ РїР°РјСЏС‚Рё > 50 MB
    ''')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.leak
    @pytest.mark.timeout(720)  # 12 РјРёРЅСѓС‚ С‚Р°Р№РјР°СѓС‚ (10 РјРёРЅ С‚РµСЃС‚ + Р·Р°РїР°СЃ)
    def test_app_with_leak_10min(self, app_with_leak_container):
        """
        РўРµСЃС‚ РїСЂРёР»РѕР¶РµРЅРёСЏ РЎ СѓС‚РµС‡РєРѕР№ - 10 РјРёРЅСѓС‚
        """
        container = app_with_leak_container
        duration = 600  # 10 РјРёРЅСѓС‚
        base_url = "http://localhost:5000"
        
        # РРЅРёС†РёР°Р»РёР·Р°С†РёСЏ
        monitor = EnhancedMemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("РќР°С‡Р°Р»Рѕ С‚РµСЃС‚Р° - Р·Р°РїРёСЃСЊ РЅР°С‡Р°Р»СЊРЅРѕРіРѕ СЃРѕСЃС‚РѕСЏРЅРёСЏ"):
            initial_memory = monitor.get_current_memory()
            allure.attach(
                f"RSS: {initial_memory['rss_mb']:.2f} MB\n"
                f"VMS: {initial_memory['vms_mb']:.2f} MB",
                name="РќР°С‡Р°Р»СЊРЅР°СЏ РїР°РјСЏС‚СЊ",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step(f"Р“РµРЅРµСЂР°С†РёСЏ РЅР°РіСЂСѓР·РєРё РІ С‚РµС‡РµРЅРёРµ {duration} СЃРµРєСѓРЅРґ"):
            memory_data = []
            start_time = time.time()
            
            # Р—Р°РїСѓСЃРєР°РµРј РіРµРЅРµСЂР°С‚РѕСЂ РЅР°РіСЂСѓР·РєРё РІ РѕС‚РґРµР»СЊРЅРѕРј РїРѕС‚РѕРєРµ
            load_gen.start(
                endpoints=['/api/cache', '/api/database', '/api/file', '/api/stress'],
                rps=5,  # 5 Р·Р°РїСЂРѕСЃРѕРІ РІ СЃРµРєСѓРЅРґСѓ
                duration=duration
            )
            
            # РњРѕРЅРёС‚РѕСЂРёРј РїР°РјСЏС‚СЊ РєР°Р¶РґС‹Рµ 5 СЃРµРєСѓРЅРґ
            while time.time() - start_time < duration:
                mem = monitor.get_current_memory()
                elapsed = time.time() - start_time
                
                memory_data.append({
                    'time': elapsed,
                    'rss_mb': mem['rss_mb'],
                    'vms_mb': mem['vms_mb'],
                    'percent': mem['percent']
                })
                
                # Р›РѕРіРёСЂСѓРµРј РєР°Р¶РґСѓСЋ РјРёРЅСѓС‚Сѓ
                if int(elapsed) % 60 == 0:
                    print(f"вЏ±пёЏ  {int(elapsed/60)} РјРёРЅ: RSS={mem['rss_mb']:.2f} MB, "
                          f"VMS={mem['vms_mb']:.2f} MB, CPU={mem['percent']:.1f}%")
                
                time.sleep(5)
            
            load_gen.stop()
        
        with allure.step("РђРЅР°Р»РёР· СЂРµР·СѓР»СЊС‚Р°С‚РѕРІ"):
            final_memory = monitor.get_current_memory()
            memory_growth = final_memory['rss_mb'] - initial_memory['rss_mb']
            
            # РЎС‚СЂРѕРёРј РіСЂР°С„РёРєРё
            chart_path = report.create_memory_chart(
                memory_data,
                title="РџРѕС‚СЂРµР±Р»РµРЅРёРµ РїР°РјСЏС‚Рё - App WITH Leak (10 min)",
                filename="memory_with_leak_10min.png"
            )
            allure.attach.file(chart_path, name="Р“СЂР°С„РёРє РїР°РјСЏС‚Рё", attachment_type=allure.attachment_type.PNG)
            
            # РђРЅР°Р»РёР· С‚СЂРµРЅРґР°
            trend_analysis = report.analyze_trend(memory_data)
            allure.attach(
                f"Р РѕСЃС‚ РїР°РјСЏС‚Рё: {memory_growth:.2f} MB\n"
                f"РўСЂРµРЅРґ: {trend_analysis['trend']}\n"
                f"РЎРєРѕСЂРѕСЃС‚СЊ СЂРѕСЃС‚Р°: {trend_analysis['growth_rate']:.2f} MB/РјРёРЅ\n"
                f"РљРѕСЌС„С„РёС†РёРµРЅС‚ СЂРѕСЃС‚Р°: {trend_analysis['growth_coefficient']:.4f}",
                name="РђРЅР°Р»РёР· С‚СЂРµРЅРґР°",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # РЎС‚Р°С‚РёСЃС‚РёРєР° РЅР°РіСЂСѓР·РєРё
            load_stats = load_gen.get_statistics()
            allure.attach(
                f"Р’СЃРµРіРѕ Р·Р°РїСЂРѕСЃРѕРІ: {load_stats['total_requests']}\n"
                f"РЈСЃРїРµС€РЅС‹С…: {load_stats['successful']}\n"
                f"РћС€РёР±РѕРє: {load_stats['errors']}\n"
                f"РЎСЂРµРґРЅРµРµ РІСЂРµРјСЏ РѕС‚РІРµС‚Р°: {load_stats['avg_response_time']:.3f} СЃРµРє",
                name="РЎС‚Р°С‚РёСЃС‚РёРєР° РЅР°РіСЂСѓР·РєРё",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Р’РµСЂРґРёРєС‚: РћР±РЅР°СЂСѓР¶РµРЅР° Р»Рё СѓС‚РµС‡РєР°?"):
            # РљСЂРёС‚РµСЂРёРё СѓС‚РµС‡РєРё:
            # 1. Р РѕСЃС‚ РїР°РјСЏС‚Рё > 50 MB
            # 2. РџРѕСЃС‚РѕСЏРЅРЅС‹Р№ РІРѕСЃС…РѕРґСЏС‰РёР№ С‚СЂРµРЅРґ
            # 3. РЎРєРѕСЂРѕСЃС‚СЊ СЂРѕСЃС‚Р° > 3 MB/РјРёРЅ
            
            is_leak = (
                memory_growth > 50 and
                trend_analysis['trend'] == 'increasing' and
                trend_analysis['growth_rate'] > 3.0
            )
            
            verdict = "рџ”ґ РЈРўР•Р§РљРђ РћР‘РќРђР РЈР–Р•РќРђ" if is_leak else "рџџў РЈС‚РµС‡РєР° РЅРµ РѕР±РЅР°СЂСѓР¶РµРЅР°"
            
            allure.attach(
                f"{verdict}\n\n"
                f"РљСЂРёС‚РµСЂРёРё:\n"
                f"вњ“ Р РѕСЃС‚ > 50 MB: {'Р”Рђ' if memory_growth > 50 else 'РќР•Рў'} ({memory_growth:.2f} MB)\n"
                f"вњ“ РўСЂРµРЅРґ СЂР°СЃС‚СѓС‰РёР№: {'Р”Рђ' if trend_analysis['trend'] == 'increasing' else 'РќР•Рў'}\n"
                f"вњ“ РЎРєРѕСЂРѕСЃС‚СЊ > 3 MB/РјРёРЅ: {'Р”Рђ' if trend_analysis['growth_rate'] > 3.0 else 'РќР•Рў'} "
                f"({trend_analysis['growth_rate']:.2f} MB/РјРёРЅ)",
                name="рџЋЇ Р’Р•Р Р”РРљРў",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # РћР¶РёРґР°РµРј РЅР°Р№С‚Рё СѓС‚РµС‡РєСѓ
            assert is_leak, f"РћР¶РёРґР°Р»Р°СЃСЊ СѓС‚РµС‡РєР° РїР°РјСЏС‚Рё, РЅРѕ СЂРѕСЃС‚ РІСЃРµРіРѕ {memory_growth:.2f} MB"
    
    
    @allure.title('РћР±РЅР°СЂСѓР¶РµРЅРёРµ СѓС‚РµС‡РєРё РїР°РјСЏС‚Рё - РџСЂРёР»РѕР¶РµРЅРёРµ Р‘Р•Р— СѓС‚РµС‡РєРё (10 РјРёРЅСѓС‚)')
    @allure.description('''
    РўРµСЃС‚ Р·Р°РїСѓСЃРєР°РµС‚ РїСЂРёР»РѕР¶РµРЅРёРµ Р‘Р•Р— СѓС‚РµС‡РµРє РїР°РјСЏС‚Рё РЅР° 10 РјРёРЅСѓС‚.
    Р“РµРЅРµСЂРёСЂСѓРµС‚ Р°РЅР°Р»РѕРіРёС‡РЅСѓСЋ РЅР°РіСЂСѓР·РєСѓ РЅР° endpoints:
    - /api/cache - cache СЃ TTL
    - /api/database - connection pool
    - /api/file - context managers
    - /api/redis - РїРµСЂРµРёСЃРїРѕР»СЊР·СѓРµРјС‹Р№ РєР»РёРµРЅС‚
    
    РћР¶РёРґР°РµС‚СЃСЏ: РЎС‚Р°Р±РёР»СЊРЅРѕРµ РїРѕС‚СЂРµР±Р»РµРЅРёРµ РїР°РјСЏС‚Рё (< 30 MB СЂРѕСЃС‚Р°)
    ''')
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.leak
    @pytest.mark.timeout(720)
    def test_app_without_leak_10min(self, app_without_leak_container):
        """
        РўРµСЃС‚ РїСЂРёР»РѕР¶РµРЅРёСЏ Р‘Р•Р— СѓС‚РµС‡РєРё - 10 РјРёРЅСѓС‚
        """
        container = app_without_leak_container
        duration = 600  # 10 РјРёРЅСѓС‚
        base_url = "http://localhost:5001"
        
        monitor = EnhancedMemoryMonitor(container)
        load_gen = LoadGenerator(base_url)
        report = ReportBuilder()
        
        with allure.step("РќР°С‡Р°Р»Рѕ С‚РµСЃС‚Р° - Р·Р°РїРёСЃСЊ РЅР°С‡Р°Р»СЊРЅРѕРіРѕ СЃРѕСЃС‚РѕСЏРЅРёСЏ"):
            initial_memory = monitor.get_current_memory()
            allure.attach(
                f"RSS: {initial_memory['rss_mb']:.2f} MB\n"
                f"VMS: {initial_memory['vms_mb']:.2f} MB",
                name="РќР°С‡Р°Р»СЊРЅР°СЏ РїР°РјСЏС‚СЊ",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step(f"Р“РµРЅРµСЂР°С†РёСЏ РЅР°РіСЂСѓР·РєРё РІ С‚РµС‡РµРЅРёРµ {duration} СЃРµРєСѓРЅРґ"):
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
                    print(f"вЏ±пёЏ  {int(elapsed/60)} РјРёРЅ: RSS={mem['rss_mb']:.2f} MB, "
                          f"VMS={mem['vms_mb']:.2f} MB, CPU={mem['percent']:.1f}%")
                
                time.sleep(5)
            
            load_gen.stop()
        
        with allure.step("РђРЅР°Р»РёР· СЂРµР·СѓР»СЊС‚Р°С‚РѕРІ"):
            final_memory = monitor.get_current_memory()
            memory_growth = final_memory['rss_mb'] - initial_memory['rss_mb']
            
            chart_path = report.create_memory_chart(
                memory_data,
                title="РџРѕС‚СЂРµР±Р»РµРЅРёРµ РїР°РјСЏС‚Рё - App WITHOUT Leak (10 min)",
                filename="memory_without_leak_10min.png"
            )
            allure.attach.file(chart_path, name="Р“СЂР°С„РёРє РїР°РјСЏС‚Рё", attachment_type=allure.attachment_type.PNG)
            
            trend_analysis = report.analyze_trend(memory_data)
            allure.attach(
                f"Р РѕСЃС‚ РїР°РјСЏС‚Рё: {memory_growth:.2f} MB\n"
                f"РўСЂРµРЅРґ: {trend_analysis['trend']}\n"
                f"РЎРєРѕСЂРѕСЃС‚СЊ СЂРѕСЃС‚Р°: {trend_analysis['growth_rate']:.2f} MB/РјРёРЅ\n"
                f"РљРѕСЌС„С„РёС†РёРµРЅС‚ СЂРѕСЃС‚Р°: {trend_analysis['growth_coefficient']:.4f}",
                name="РђРЅР°Р»РёР· С‚СЂРµРЅРґР°",
                attachment_type=allure.attachment_type.TEXT
            )
            
            load_stats = load_gen.get_statistics()
            allure.attach(
                f"Р’СЃРµРіРѕ Р·Р°РїСЂРѕСЃРѕРІ: {load_stats['total_requests']}\n"
                f"РЈСЃРїРµС€РЅС‹С…: {load_stats['successful']}\n"
                f"РћС€РёР±РѕРє: {load_stats['errors']}\n"
                f"РЎСЂРµРґРЅРµРµ РІСЂРµРјСЏ РѕС‚РІРµС‚Р°: {load_stats['avg_response_time']:.3f} СЃРµРє",
                name="РЎС‚Р°С‚РёСЃС‚РёРєР° РЅР°РіСЂСѓР·РєРё",
                attachment_type=allure.attachment_type.TEXT
            )
        
        with allure.step("Р’РµСЂРґРёРєС‚: РћР±РЅР°СЂСѓР¶РµРЅР° Р»Рё СѓС‚РµС‡РєР°?"):
            is_leak = (
                memory_growth > 50 and
                trend_analysis['trend'] == 'increasing' and
                trend_analysis['growth_rate'] > 3.0
            )
            
            verdict = "рџ”ґ РЈРўР•Р§РљРђ РћР‘РќРђР РЈР–Р•РќРђ" if is_leak else "рџџў РЈС‚РµС‡РєР° РЅРµ РѕР±РЅР°СЂСѓР¶РµРЅР°"
            
            allure.attach(
                f"{verdict}\n\n"
                f"РљСЂРёС‚РµСЂРёРё:\n"
                f"вњ“ Р РѕСЃС‚ > 50 MB: {'Р”Рђ' if memory_growth > 50 else 'РќР•Рў'} ({memory_growth:.2f} MB)\n"
                f"вњ“ РўСЂРµРЅРґ СЂР°СЃС‚СѓС‰РёР№: {'Р”Рђ' if trend_analysis['trend'] == 'increasing' else 'РќР•Рў'}\n"
                f"вњ“ РЎРєРѕСЂРѕСЃС‚СЊ > 3 MB/РјРёРЅ: {'Р”Рђ' if trend_analysis['growth_rate'] > 3.0 else 'РќР•Рў'} "
                f"({trend_analysis['growth_rate']:.2f} MB/РјРёРЅ)",
                name="рџЋЇ Р’Р•Р Р”РРљРў",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # РќР• РѕР¶РёРґР°РµРј РЅР°Р№С‚Рё СѓС‚РµС‡РєСѓ
            assert not is_leak, f"РќРµРѕР¶РёРґР°РЅРЅР°СЏ СѓС‚РµС‡РєР° РїР°РјСЏС‚Рё: СЂРѕСЃС‚ {memory_growth:.2f} MB"
    
    
    @allure.title('РЎСЂР°РІРЅРёС‚РµР»СЊРЅС‹Р№ С‚РµСЃС‚ - 15 РјРёРЅСѓС‚')
    @allure.description('Р—Р°РїСѓСЃРєР°РµС‚ РѕР±Р° РїСЂРёР»РѕР¶РµРЅРёСЏ РѕРґРЅРѕРІСЂРµРјРµРЅРЅРѕ РґР»СЏ СЃСЂР°РІРЅРµРЅРёСЏ')
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.slow
    @pytest.mark.timeout(1080)  # 18 РјРёРЅСѓС‚
    def test_comparative_15min(self, app_with_leak_container, app_without_leak_container):
        """
        РЎСЂР°РІРЅРёС‚РµР»СЊРЅС‹Р№ С‚РµСЃС‚ РѕР±РѕРёС… РїСЂРёР»РѕР¶РµРЅРёР№ - 15 РјРёРЅСѓС‚
        """
        duration = 900  # 15 РјРёРЅСѓС‚
        
        # РњРѕРЅРёС‚РѕСЂС‹
        monitor_leak = EnhancedMemoryMonitor(app_with_leak_container)
        monitor_no_leak = EnhancedMemoryMonitor(app_without_leak_container)
        
        # Р“РµРЅРµСЂР°С‚РѕСЂС‹ РЅР°РіСЂСѓР·РєРё
        load_leak = LoadGenerator("http://localhost:5000")
        load_no_leak = LoadGenerator("http://localhost:5001")
        
        report = ReportBuilder()
        
        with allure.step("Р—Р°РїСѓСЃРє РїР°СЂР°Р»Р»РµР»СЊРЅРѕРіРѕ РјРѕРЅРёС‚РѕСЂРёРЅРіР°"):
            data_leak = []
            data_no_leak = []
            
            # Р—Р°РїСѓСЃРєР°РµРј РЅР°РіСЂСѓР·РєСѓ РЅР° РѕР±Р°
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
                    print(f"вЏ±пёЏ  {int(elapsed/60)} РјРёРЅ:")
                    print(f"   WITH leak: RSS={mem_leak['rss_mb']:.2f} MB")
                    print(f"   WITHOUT leak: RSS={mem_no_leak['rss_mb']:.2f} MB")
                
                time.sleep(5)
            
            load_leak.stop()
            load_no_leak.stop()
        
        with allure.step("РЎСЂР°РІРЅРёС‚РµР»СЊРЅС‹Р№ Р°РЅР°Р»РёР·"):
            # РЎРѕР·РґР°РµРј СЃСЂР°РІРЅРёС‚РµР»СЊРЅС‹Р№ РіСЂР°С„РёРє
            chart_path = report.create_comparison_chart(
                data_leak,
                data_no_leak,
                title="РЎСЂР°РІРЅРµРЅРёРµ РїРѕС‚СЂРµР±Р»РµРЅРёСЏ РїР°РјСЏС‚Рё (15 min)",
                filename="memory_comparison_15min.png"
            )
            allure.attach.file(chart_path, name="РЎСЂР°РІРЅРёС‚РµР»СЊРЅС‹Р№ РіСЂР°С„РёРє", attachment_type=allure.attachment_type.PNG)
            
            # РђРЅР°Р»РёР· С‚СЂРµРЅРґРѕРІ
            trend_leak = report.analyze_trend(data_leak)
            trend_no_leak = report.analyze_trend(data_no_leak)
            
            growth_leak = data_leak[-1]['rss_mb'] - data_leak[0]['rss_mb']
            growth_no_leak = data_no_leak[-1]['rss_mb'] - data_no_leak[0]['rss_mb']
            
            allure.attach(
                f"рџ“Љ РЎР РђР’РќРРўР•Р›Р¬РќР«Р™ РћРўР§Р•Рў\n\n"
                f"РЎ РЈРўР•Р§РљРћР™:\n"
                f"  Р РѕСЃС‚ РїР°РјСЏС‚Рё: {growth_leak:.2f} MB\n"
                f"  РЎРєРѕСЂРѕСЃС‚СЊ: {trend_leak['growth_rate']:.2f} MB/РјРёРЅ\n"
                f"  РўСЂРµРЅРґ: {trend_leak['trend']}\n\n"
                f"Р‘Р•Р— РЈРўР•Р§РљР:\n"
                f"  Р РѕСЃС‚ РїР°РјСЏС‚Рё: {growth_no_leak:.2f} MB\n"
                f"  РЎРєРѕСЂРѕСЃС‚СЊ: {trend_no_leak['growth_rate']:.2f} MB/РјРёРЅ\n"
                f"  РўСЂРµРЅРґ: {trend_no_leak['trend']}\n\n"
                f"Р РђР—РќРР¦Рђ:\n"
                f"  Р РѕСЃС‚ РїР°РјСЏС‚Рё: {growth_leak - growth_no_leak:.2f} MB\n"
                f"  РЎРѕРѕС‚РЅРѕС€РµРЅРёРµ: {growth_leak / max(growth_no_leak, 1):.2f}x",
                name="рџ“€ РЎСЂР°РІРЅРёС‚РµР»СЊРЅС‹Р№ Р°РЅР°Р»РёР·",
                attachment_type=allure.attachment_type.TEXT
            )
