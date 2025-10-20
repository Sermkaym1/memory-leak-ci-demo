"""
Pytest конфигурация и fixtures для тестов утечек памяти
"""
import pytest
import docker
import time
import os
import requests
from typing import Generator

# Инициализация Docker клиента
docker_client = docker.from_env()


def wait_for_service_health(url: str, service_name: str, max_wait: int = 60) -> bool:
    """
    Умная проверка готовности сервиса через HTTP healthcheck
    Возвращает True как только сервис отвечает, не ждет фиксированное время
    """
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
        
        print(f"⏳ {service_name} еще не готов, жду... ({int(time.time() - start_time)}с)")
        time.sleep(2)
    
    print(f"❌ {service_name} не готов за {max_wait} сек")
    return False


@pytest.fixture(scope="session")
def ensure_services_running():
    """
    Убеждаемся что все сервисы запущены перед тестами
    УМНАЯ проверка - не ждет фиксированное время, а проверяет готовность
    Поддерживает CI окружения где контейнеры могут иметь префиксы
    """
    print("\n🔍 Проверка Docker сервисов...")
    
    required_containers = [
        'app-with-leak',
        'app-without-leak'
    ]
    
    # Проверяем и запускаем контейнеры
    for container_name in required_containers:
        try:
            container = docker_client.containers.get(container_name)
            if container.status != 'running':
                print(f"⚠️  {container_name} не запущен, запускаю...")
                container.start()
                time.sleep(2)  # Минимальная пауза для старта
            else:
                print(f"✅ {container_name} уже работает")
        except docker.errors.NotFound:
            # В CI контейнеры могут иметь префиксы проекта
            print(f"⚠️  Контейнер {container_name} не найден по точному имени")
            print("🔍 Поищем контейнеры с похожими именами...")
            
            # Ищем контейнеры с похожими именами
            all_containers = docker_client.containers.list(all=True)
            found = False
            for c in all_containers:
                if container_name in c.name or any(container_name in tag for tag in c.image.tags):
                    print(f"🎯 Найден похожий контейнер: {c.name} (статус: {c.status})")
                    if c.status != 'running':
                        print(f"⚠️  Запускаю {c.name}...")
                        c.start()
                        time.sleep(2)
                    found = True
                    break
            
            if not found:
                print(f"❌ Контейнер с именем {container_name} не найден!")
                print("📋 Доступные контейнеры:")
                for c in all_containers:
                    print(f"  - {c.name} ({c.status})")
                print("\n💡 Запустите: docker compose up -d app-with-leak app-without-leak")
    
    # Умная проверка готовности сервисов через HTTP
    print("\n🎯 УМНАЯ ПРОВЕРКА готовности сервисов (без лишних ожиданий):")
    
    services_to_check = [
        ("http://localhost:5000/health", "App WITH leak"),
        ("http://localhost:5001/health", "App WITHOUT leak")
    ]
    
    all_ready = True
    for url, name in services_to_check:
        if not wait_for_service_health(url, name, max_wait=30):
            all_ready = False
    
    if not all_ready:
        pytest.fail("❌ Не все сервисы готовы к тестированию")
    
    print("🚀 ВСЕ СЕРВИСЫ ГОТОВЫ! Запускаем тесты...\n")


@pytest.fixture
def app_with_leak_container(ensure_services_running) -> Generator:
    """
    Fixture для контейнера с утечкой памяти
    БЕЗ перезапуска - используем уже готовый контейнер
    Поддерживает поиск контейнеров с префиксами проекта
    """
    container = None
    try:
        container = docker_client.containers.get('app-with-leak')
    except docker.errors.NotFound:
        # Ищем контейнер с похожим именем
        all_containers = docker_client.containers.list(all=True)
        for c in all_containers:
            if 'app-with-leak' in c.name or 'app_with_leak' in c.name:
                container = c
                break
        
        if not container:
            pytest.fail("❌ Контейнер app-with-leak не найден")
    
    print(f"🔴 Используем контейнер {container.name} (С УТЕЧКОЙ)")
    
    # Проверяем что контейнер здоров, без перезапуска
    if not wait_for_service_health("http://localhost:5000/health", "App WITH leak", max_wait=10):
        print("⚠️  Сервис не отвечает, попробуем перезапустить...")
        container.restart()
        wait_for_service_health("http://localhost:5000/health", "App WITH leak", max_wait=20)
    
    yield container
    
    # Cleanup - просто логируем
    print("✅ Тест с утечкой завершен")


@pytest.fixture
def app_without_leak_container(ensure_services_running) -> Generator:
    """
    Fixture для контейнера без утечки памяти
    БЕЗ перезапуска - используем уже готовый контейнер
    Поддерживает поиск контейнеров с префиксами проекта
    """
    container = None
    try:
        container = docker_client.containers.get('app-without-leak')
    except docker.errors.NotFound:
        # Ищем контейнер с похожим именем
        all_containers = docker_client.containers.list(all=True)
        for c in all_containers:
            if 'app-without-leak' in c.name or 'app_without_leak' in c.name:
                container = c
                break
        
        if not container:
            pytest.fail("❌ Контейнер app-without-leak не найден")
    
    print(f"🟢 Используем контейнер {container.name} (БЕЗ УТЕЧКИ)")
    
    # Проверяем что контейнер здоров, без перезапуска
    if not wait_for_service_health("http://localhost:5001/health", "App WITHOUT leak", max_wait=10):
        print("⚠️  Сервис не отвечает, попробуем перезапустить...")
        container.restart()
        wait_for_service_health("http://localhost:5001/health", "App WITHOUT leak", max_wait=20)
    
    yield container
    
    # Cleanup - просто логируем
    print("✅ Тест без утечки завершен")


def pytest_configure(config):
    """
    Pytest конфигурация
    """
    # Создаем директорию для Allure результатов
    os.makedirs("tests/allure-results", exist_ok=True)
    
    # Добавляем кастомные маркеры
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "leak: marks tests that check for memory leaks")
