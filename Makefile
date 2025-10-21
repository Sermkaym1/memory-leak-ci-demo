# ==========================================
# Memory Leak CI Demo - Makefile
# Запуск всего проекта "одной кнопкой"
# ==========================================

.PHONY: help install build up down test report clean logs status full-demo quick-demo

# Цвета для вывода
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Переменные
PYTHON := python3
VENV := venv
ALLURE_RESULTS := tests/allure-results
ALLURE_REPORT := tests/allure-report

##@ Основные команды (Quick Start)

help: ## 📖 Показать это меню помощи
	@echo ""
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║  Memory Leak CI Demo - Автоматизированное управление      ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Использование:\n  make $(BLUE)<команда>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

demo: ## 🎬 ДЕМО ЗАПУСК (30 секунд) - ГЛАВНАЯ КОМАНДА ДЛЯ ПРЕЗЕНТАЦИЙ!
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║              🎬 ДЕМО ДЛЯ ПРЕЗЕНТАЦИЙ                      ║$(NC)"
	@echo "$(GREEN)║                   (30 секунд)                             ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)⚡ Быстрый демо показ для презентаций$(NC)"
	@echo "$(BLUE)📋 Что произойдет:$(NC)"
	@echo "  1️⃣  Сборка контейнеров (30 сек)"
	@echo "  2️⃣  Быстрые тесты (30 сек)"
	@echo "  3️⃣  Генерация красивого отчета"
	@echo ""
	@make build
	@make up
	@$(PYTHON) -m pytest tests/test_demo.py -v --alluredir=$(ALLURE_RESULTS)
	@make report-generate
	@echo "$(GREEN)🎉 Демо готово! Отчет: $(ALLURE_REPORT)/index.html$(NC)"

full-demo: ## 🚀 ПОЛНЫЙ ЗАПУСК (установка + полные тесты + отчет)
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║           🚀 ПОЛНЫЙ АНАЛИЗ ПРОЕКТА                        ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Это займет ~5-10 минут (полные тесты)$(NC)"
	@echo ""
	@make install
	@make build
	@make up
	@make test
	@make report

quick-demo: ## ⚡ БЫСТРЫЕ ТЕСТЫ (3 минуты с мониторингом)
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║              ⚡ БЫСТРЫЕ ТЕСТЫ                              ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@make build
	@make up
	@$(PYTHON) -m pytest tests/test_quick_demo.py -v --alluredir=$(ALLURE_RESULTS)
	@make report

##@ Установка и настройка

install: ## 📦 Установить все зависимости (Python + Allure)
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	@bash scripts/install.sh

check-requirements: ## ✅ Проверить что все требования установлены
	@echo "$(BLUE)🔍 Проверка требований...$(NC)"
	@bash scripts/check-requirements.sh

##@ Docker контейнеры

build: ## 🔨 Собрать Docker образы
	@echo "$(BLUE)🔨 Сборка Docker образов...$(NC)"
	docker-compose build --parallel

up: ## ▶️  Запустить все сервисы (приложения + мониторинг)
	@echo "$(GREEN)▶️  Запуск всех сервисов...$(NC)"
	docker-compose up -d
	@echo ""
	@echo "$(YELLOW)⏳ Ожидание готовности сервисов (30 сек)...$(NC)"
	@sleep 30
	@make status
	@echo ""
	@echo "$(GREEN)✅ Все сервисы запущены!$(NC)"
	@echo ""
	@echo "Доступные URL:"
	@echo "  🔴 App WITH leak:    $(BLUE)http://localhost:5000/health$(NC)"
	@echo "  🟢 App WITHOUT leak: $(BLUE)http://localhost:5001/health$(NC)"
	@echo "  📊 Prometheus:       $(BLUE)http://localhost:9090$(NC)"
	@echo "  📈 Grafana:          $(BLUE)http://localhost:3000$(NC) (admin/admin)"
	@echo ""

down: ## ⏹️  Остановить все сервисы
	@echo "$(RED)⏹️  Остановка всех сервисов...$(NC)"
	docker-compose down

restart: down up ## 🔄 Перезапустить все сервисы

status: ## 📊 Показать статус всех сервисов
	@echo "$(BLUE)📊 Статус сервисов:$(NC)"
	@docker-compose ps

logs: ## 📜 Показать логи всех сервисов
	docker-compose logs -f

logs-leak: ## 📜 Показать логи приложения С утечкой
	docker-compose logs -f app-with-leak

logs-no-leak: ## 📜 Показать логи приложения БЕЗ утечки
	docker-compose logs -f app-without-leak

##@ Тестирование

test: ## 🧪 Запустить ВСЕ тесты (10-15 минут)
	@echo "$(GREEN)🧪 Запуск полных тестов (это займет 10-15 минут)...$(NC)"
	@echo ""
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		echo "$(YELLOW)Запустите: make install$(NC)"; \
		exit 1; \
	fi
	@. $(VENV)/bin/activate && pytest tests/test_memory_leak.py -v -s --alluredir=$(ALLURE_RESULTS)
	@echo ""
	@echo "$(GREEN)✅ Тесты завершены! Смотрите отчет: make report$(NC)"

test-quick: ## ⚡ Запустить быстрые тесты (5 минут) с НАБЛЮДАЕМОСТЬЮ
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║           ⚡ БЫСТРЫЕ ТЕСТЫ С НАБЛЮДАЕМОСТЬЮ                ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)📋 Что будет происходить:$(NC)"
	@echo "  1️⃣  Проверка готовности сервисов (БЕЗ долгих ожиданий)"
	@echo "  2️⃣  Тест приложения С утечкой (5 мин) с прогресс-баром"
	@echo "  3️⃣  Тест приложения БЕЗ утечки (5 мин) с прогресс-баром"
	@echo "  4️⃣  Генерация отчета с графиками"
	@echo ""
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(RED)❌ Виртуальное окружение не найдено!$(NC)"; \
		echo "$(YELLOW)Запустите: make install$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)🚀 Запускаем быстрые тесты с улучшенной наблюдаемостью...$(NC)"
	@. $(VENV)/bin/activate && pytest tests/test_quick_demo.py -v -s --tb=short --alluredir=$(ALLURE_RESULTS)
	@echo ""
	@echo "$(GREEN)✅ Быстрые тесты завершены! Отчет: make report$(NC)"

test-one: ## 🎯 Запустить один конкретный тест
	@echo "$(BLUE)Доступные тесты:$(NC)"
	@echo "  1) test_app_with_leak_10min"
	@echo "  2) test_app_without_leak_10min"
	@echo "  3) test_comparative_15min"
	@read -p "Выберите номер теста: " test_num; \
	case $$test_num in \
		1) TEST="test_app_with_leak_10min" ;; \
		2) TEST="test_app_without_leak_10min" ;; \
		3) TEST="test_comparative_15min" ;; \
		*) echo "$(RED)Неверный выбор$(NC)"; exit 1 ;; \
	esac; \
	. $(VENV)/bin/activate && pytest tests/test_memory_leak.py::TestMemoryLeakDetection::$$TEST -v -s --alluredir=$(ALLURE_RESULTS)

##@ Отчеты

report: ## 📊 Открыть Allure отчет в браузере
	@if [ ! -d "$(ALLURE_RESULTS)" ] || [ -z "$$(ls -A $(ALLURE_RESULTS))" ]; then \
		echo "$(RED)❌ Нет результатов тестов!$(NC)"; \
		echo "$(YELLOW)Сначала запустите: make test$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)📊 Генерация и открытие Allure отчета...$(NC)"
	@allure serve $(ALLURE_RESULTS)

report-generate: ## 📄 Сгенерировать статический HTML отчет
	@echo "$(BLUE)📄 Генерация статического отчета...$(NC)"
	@allure generate $(ALLURE_RESULTS) -o $(ALLURE_REPORT) --clean
	@echo "$(GREEN)✅ Отчет сгенерирован в: $(ALLURE_REPORT)/index.html$(NC)"

##@ Мониторинг

open-grafana: ## 📈 Открыть Grafana в браузере (Linux)
	@echo "$(BLUE)📈 Открытие Grafana...$(NC)"
	@echo "URL: http://localhost:3000"
	@echo "Login: admin"
	@echo "Password: admin"
	@xdg-open http://localhost:3000 2>/dev/null || echo "Откройте вручную: http://localhost:3000"

open-prometheus: ## 📊 Открыть Prometheus в браузере (Linux)
	@echo "$(BLUE)📊 Открытие Prometheus...$(NC)"
	@xdg-open http://localhost:9090 2>/dev/null || echo "Откройте вручную: http://localhost:9090"

monitor: ## 👁️  Живой мониторинг памяти (Ctrl+C для выхода)
	@echo "$(BLUE)👁️  Мониторинг памяти контейнеров (обновление каждые 5 сек)...$(NC)"
	@bash scripts/live-monitor.sh

##@ Очистка

clean: ## 🧹 Очистить результаты тестов и отчеты
	@echo "$(YELLOW)🧹 Очистка результатов тестов...$(NC)"
	rm -rf $(ALLURE_RESULTS)
	rm -rf $(ALLURE_REPORT)
	rm -rf tests/allure-results/*.png
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

clean-all: down clean ## 🗑️  Полная очистка (контейнеры + volumes + результаты)
	@echo "$(RED)🗑️  ПОЛНАЯ ОЧИСТКА всех данных...$(NC)"
	@read -p "Удалить ВСЕ данные (контейнеры, volumes, результаты)? (y/n): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose down -v
	docker system prune -f
	rm -rf $(VENV)
	@echo "$(GREEN)✅ Полная очистка завершена$(NC)"

##@ Разработка

shell-leak: ## 🐚 Открыть shell в контейнере С утечкой
	docker exec -it app-with-leak /bin/sh

shell-no-leak: ## 🐚 Открыть shell в контейнере БЕЗ утечки
	docker exec -it app-without-leak /bin/sh

db-shell: ## 🐚 Подключиться к PostgreSQL
	docker exec -it postgres-leak-demo psql -U testuser -d testdb

redis-shell: ## 🐚 Подключиться к Redis
	docker exec -it redis-leak-demo redis-cli

##@ Информация

info: ## ℹ️  Показать информацию о проекте
	@echo ""
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║         Memory Leak CI Demo Project                       ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(BLUE)Автор:$(NC) @Sermkaym1"
	@echo "$(BLUE)Дата:$(NC) 2025-10-19"
	@echo ""
	@echo "$(YELLOW)Структура проекта:$(NC)"
	@tree -L 2 -I 'venv|__pycache__|*.pyc|allure-*' || ls -R
	@echo ""

docs: ## 📚 Открыть документацию
	@echo "$(BLUE)📚 Документация:$(NC)"
	@echo ""
	@echo "  README.md - Основная документация"
	@echo "  docs/QUICK_START.md - Быстрый старт"
	@echo "  docs/MEMORY_LEAK_PATTERNS.md - Паттерны утечек"
	@echo ""
