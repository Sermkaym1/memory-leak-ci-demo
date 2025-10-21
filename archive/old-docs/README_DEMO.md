# 🚀 Demo CI/CD Memory Leak Detection

Быстрая демо-система для обнаружения утечек памяти в CI/CD.

## ⚡ Быстрый старт (30 секунд)

```bash
# Запуск демо локально
python test_demo_local.py

# Или через GitHub Actions
git push origin main  # Автоматически запустится demo-ci.yml
```

## 🎯 Что делает демо

1. **Сборка (15 сек)**: Собирает два Docker контейнера
   - `app-with-leak` - приложение С утечкой памяти  
   - `app-without-leak` - приложение БЕЗ утечки

2. **Тестирование (30 сек)**: Быстрые тесты на утечки
   - Нагрузка на приложения
   - Мониторинг памяти
   - Четкий вердикт: "LEAK DETECTED" vs "HEALTHY APP"

3. **Отчеты**: Красивые графики и Allure отчеты

## 📊 Результат

```
🔴 App WITH leak: LEAK DETECTED (memory +45MB)
🟢 App WITHOUT leak: HEALTHY APP (memory stable)
```

## 🔧 Технологии

- **CI/CD**: GitHub Actions (1-2 минуты общее время)
- **Контейнеризация**: Docker + Docker Compose
- **Тестирование**: pytest + allure-pytest + pytest-timeout
- **Мониторинг**: EnhancedMemoryMonitor с визуализацией
- **Отчеты**: Allure + matplotlib графики

## 📁 Структура

```
tests/
├── test_demo.py          # 30-секундные демо тесты
├── conftest.py           # Docker fixtures
└── utils/
    ├── enhanced_monitor.py   # Мониторинг памяти
    ├── load_generator.py     # Генератор нагрузки  
    └── report_builder.py     # Построение отчетов

.github/workflows/
├── demo-ci.yml           # Быстрый демо CI (1-2 мин)
└── memory-leak-ci.yml    # Полный CI (10+ мин)
```

## 🚀 Режимы запуска

- **Demo** (30 сек): `test_demo.py` - для презентаций
- **Quick** (2 мин): Быстрые тесты с базовой проверкой
- **Full** (10+ мин): Полное тестирование с глубоким анализом

## 🐛 Отладка

Если что-то не работает:

```bash
# Проверить контейнеры
docker ps
docker logs app-with-leak
docker logs app-without-leak

# Перезапустить демо
docker compose down
docker compose up -d app-with-leak app-without-leak

# Тесты вручную
python -m pytest tests/test_demo.py -v
```

Создано для демонстрации современного CI/CD с автоматическим обнаружением утечек памяти! 🎉