#!/bin/bash

# ==========================================
# Скрипт автоматической установки всех зависимостей
# ==========================================

set -e  # Выход при ошибке

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Установка зависимостей Memory Leak CI Demo            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Функция для проверки команды
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Функция для установки с подтверждением
install_with_confirm() {
    local package=$1
    local install_cmd=$2
    
    echo -e "${YELLOW}❓ $package не установлен. Установить? (y/n)${NC}"
    read -p "> " confirm
    if [ "$confirm" = "y" ]; then
        echo -e "${BLUE}📦 Установка $package...${NC}"
        eval "$install_cmd"
        echo -e "${GREEN}✅ $package установлен${NC}"
    else
        echo -e "${RED}⚠️  $package пропущен. Проект может работать некорректно.${NC}"
    fi
}

# 1. Проверка Python
echo -e "${BLUE}🐍 Проверка Python...${NC}"
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python установлен: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python3 не найден!${NC}"
    install_with_confirm "Python3" "sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
fi

# 2. Проверка Docker
echo -e "${BLUE}🐳 Проверка Docker...${NC}"
if command_exists docker; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    echo -e "${GREEN}✅ Docker установлен: $DOCKER_VERSION${NC}"
    
    # Проверка прав
    if groups $USER | grep -q docker; then
        echo -e "${GREEN}✅ Пользователь в группе docker${NC}"
    else
        echo -e "${YELLOW}⚠️  Добавление пользователя в группу docker...${NC}"
        sudo usermod -aG docker $USER
        echo -e "${YELLOW}⚠️  ВАЖНО: Перелогиньтесь для применения изменений!${NC}"
    fi
else
    echo -e "${RED}❌ Docker не найден!${NC}"
    install_with_confirm "Docker" "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker $USER"
fi

# 3. Проверка Docker Compose
echo -e "${BLUE}🐳 Проверка Docker Compose...${NC}"
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker Compose установлен${NC}"
else
    echo -e "${RED}❌ Docker Compose не найден!${NC}"
    install_with_confirm "Docker Compose" \
        'sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose'
fi

# 4. Проверка Java (для Allure)
echo -e "${BLUE}☕ Проверка Java...${NC}"
if command_exists java; then
    JAVA_VERSION=$(java -version 2>&1 | head -n 1)
    echo -e "${GREEN}✅ Java установлена: $JAVA_VERSION${NC}"
else
    echo -e "${RED}❌ Java не найдена!${NC}"
    install_with_confirm "Java (OpenJDK 11)" "sudo apt update && sudo apt install -y openjdk-11-jdk"
fi

# 5. Проверка Allure
echo -e "${BLUE}📊 Проверка Allure...${NC}"
if command_exists allure; then
    ALLURE_VERSION=$(allure --version)
    echo -e "${GREEN}✅ Allure установлен: $ALLURE_VERSION${NC}"
else
    echo -e "${RED}❌ Allure не найден!${NC}"
    echo -e "${YELLOW}📦 Установка Allure...${NC}"
    
    cd /tmp
    wget -q https://github.com/allure-framework/allure2/releases/download/2.24.1/allure-2.24.1.tgz
    sudo tar -zxf allure-2.24.1.tgz -C /opt/
    sudo ln -sf /opt/allure-2.24.1/bin/allure /usr/bin/allure
    rm allure-2.24.1.tgz
    
    echo -e "${GREEN}✅ Allure установлен${NC}"
fi

# 6. Создание Python виртуального окружения
echo -e "${BLUE}🔧 Настройка Python окружения...${NC}"
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Создание виртуального окружения...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
else
    echo -e "${GREEN}✅ Виртуальное окружение уже существует${NC}"
fi

# 7. Установка Python зависимостей
echo -e "${BLUE}📦 Установка Python пакетов...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Python пакеты установлены${NC}"

# 8. Создание необходимых директорий
echo -e "${BLUE}📁 Создание директорий...${NC}"
mkdir -p tests/allure-results
mkdir -p tests/allure-report
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
echo -e "${GREEN}✅ Директории созданы${NC}"

# 9. Проверка .env файла
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Создание .env файла...${NC}"
    cat > .env << 'EOF'
# Database
DB_HOST=postgres
DB_NAME=testdb
DB_USER=testuser
DB_PASSWORD=testpass

# Redis
REDIS_HOST=redis

# Grafana
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
EOF
    echo -e "${GREEN}✅ .env файл создан${NC}"
else
    echo -e "${GREEN}✅ .env файл существует${NC}"
fi

# Итоговая проверка
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✅ УСТАНОВКА ЗАВЕРШЕНА!                       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Следующие шаги:${NC}"
echo ""
echo -e "  1️⃣  Запустите полное демо:"
echo -e "     ${YELLOW}make full-demo${NC}"
echo ""
echo -e "  2️⃣  Или запустите быстрое демо (5 мин):"
echo -e "     ${YELLOW}make quick-demo${NC}"
echo ""
echo -e "  3️⃣  Или запустите по шагам:"
echo -e "     ${YELLOW}make build${NC}    # Собрать образы"
echo -e "     ${YELLOW}make up${NC}       # Запустить сервисы"
echo -e "     ${YELLOW}make test${NC}     # Запустить тесты"
echo -e "     ${YELLOW}make report${NC}   # Открыть отчет"
echo ""
echo -e "${BLUE}Справка по всем командам:${NC} ${YELLOW}make help${NC}"
echo ""

deactivate 2>/dev/null || true
