"""
Pytest конфигурация и fixtures для тестов утечек памяти
"""
import pytest
import docker
import time
import os
from typing import Generator

# Инициализация Docker клиента
docker_client = docker.from_env()


@pytest.fixture(scope="session")
def ensure_services_running():
    """
    Убеждаемся что все сервисы запущены перед тестами
    """
    print("\n🔍 Проверка Docker сервисов...")
    
    required_containers = [
        'app-with-leak',
        'app-without-leak',
        'postgres-leak-demo',
        'redis-leak-demo'
    ]
    
    for container_name in required_containers:
        try:
            container = docker_client.containers.get(container_name)
            if container.status != 'running':
                print(f"⚠️  {container_name} не запущен, запускаю...")
                container.start()
                time.sleep(5)
            else:
                print(f"✅ {container_name} работает")
        except docker.errors.NotFound:
            pytest.fail(f"❌ Контейнер {container_name} не найден. Запустите: docker-compose up -d")
    
    # Ждем готовности сервисов
    print("⏳ Ожидание готовности сервисов (30 сек)...")
    time.sleep(30)
    print("✅ Все сервисы готовы\n")


@pytest.fixture
def app_with_leak_container(ensure_services_running) -> Generator:
    """
    Fixture для контейнера с утечкой памяти
    """
    container = docker_client.containers.get('app-with-leak')
    
    # Перезапускаем контейнер для чистого состояния
    print("🔄 Перезапуск app-with-leak для чистого теста...")
    container.restart()
    time.sleep(10)
    
    yield container
    
    # Cleanup
    print("🧹 Очистка после теста...")


@pytest.fixture
def app_without_leak_container(ensure_services_running) -> Generator:
    """
    Fixture для контейнера без утечки памяти
    """
    container = docker_client.containers.get('app-without-leak')
    
    # Перезапускаем контейнер для чистого состояния
    print("🔄 Перезапуск app-without-leak для чистого теста...")
    container.restart()
    time.sleep(10)
    
    yield container
    
    # Cleanup
    print("🧹 Очистка после теста...")


def pytest_configure(config):
    """
    Pytest конфигурация
    """
    # Создаем директорию для Allure результатов
    os.makedirs("tests/allure-results", exist_ok=True)
    
    # Добавляем кастомные маркеры
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "leak: marks tests that check for memory leaks")
