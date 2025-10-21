#!/usr/bin/env python3
"""
Локальный тест демо системы
Проверяем что все работает без GitHub Actions
"""
import subprocess
import sys
import time
import requests

def run_command(cmd, description):
    """Выполняет команду и показывает результат"""
    print(f"\n🔍 {description}")
    print(f"💻 Команда: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.stdout:
            print(f"📤 Вывод:\n{result.stdout}")
        if result.stderr:
            print(f"⚠️  Ошибки:\n{result.stderr}")
            
        if result.returncode == 0:
            print(f"✅ {description} - УСПЕХ")
            return True
        else:
            print(f"❌ {description} - ОШИБКА (код: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - ТАЙМАУТ")
        return False
    except Exception as e:
        print(f"💥 {description} - ИСКЛЮЧЕНИЕ: {e}")
        return False

def check_service_health(url, name):
    """Проверяет здоровье сервиса"""
    print(f"\n🏥 Проверка здоровья {name}: {url}")
    
    for attempt in range(10):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} здоров!")
                return True
        except requests.exceptions.RequestException as e:
            print(f"⏳ Попытка {attempt + 1}/10: {name} не отвечает ({e})")
            time.sleep(3)
    
    print(f"❌ {name} не отвечает")
    return False

def main():
    """Основная функция тестирования"""
    print("🚀 ЛОКАЛЬНЫЙ ТЕСТ ДЕМО СИСТЕМЫ")
    print("=" * 50)
    
    # 1. Проверяем Docker
    if not run_command("docker --version", "Проверка Docker"):
        sys.exit(1)
    
    # 2. Проверяем Docker Compose
    if not run_command("docker compose version", "Проверка Docker Compose"):
        if not run_command("docker-compose --version", "Проверка docker-compose"):
            print("❌ Ни docker compose, ни docker-compose не найдены")
            sys.exit(1)
    
    # 3. Останавливаем старые контейнеры
    print("\n🧹 Очистка старых контейнеров...")
    run_command("docker compose down", "Остановка старых контейнеров")
    
    # 4. Собираем образы
    if not run_command("docker compose build app-with-leak app-without-leak", "Сборка образов"):
        sys.exit(1)
    
    # 5. Запускаем контейнеры
    if not run_command("docker compose up -d app-with-leak app-without-leak", "Запуск контейнеров"):
        sys.exit(1)
    
    # 6. Ждем запуска
    print("\n⏳ Ждем запуска контейнеров...")
    time.sleep(15)
    
    # 7. Проверяем статус
    run_command("docker ps", "Статус контейнеров")
    
    # 8. Проверяем здоровье сервисов
    app_with_leak_ok = check_service_health("http://localhost:5000/health", "App WITH leak")
    app_without_leak_ok = check_service_health("http://localhost:5001/health", "App WITHOUT leak")
    
    if not (app_with_leak_ok and app_without_leak_ok):
        print("\n❌ Сервисы не готовы, показываем логи:")
        run_command("docker logs app-with-leak", "Логи app-with-leak")
        run_command("docker logs app-without-leak", "Логи app-without-leak")
        sys.exit(1)
    
    # 9. Запускаем демо тесты
    if not run_command("python -m pytest tests/test_demo.py -v --tb=short --timeout=120", "Демо тесты"):
        print("\n❌ Тесты упали, показываем логи:")
        run_command("docker logs app-with-leak", "Логи app-with-leak")
        run_command("docker logs app-without-leak", "Логи app-without-leak")
        sys.exit(1)
    
    print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    print("✅ Демо система готова для GitHub Actions")

if __name__ == "__main__":
    main()