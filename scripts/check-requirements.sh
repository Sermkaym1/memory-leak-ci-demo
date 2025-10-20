#!/bin/bash

# ==========================================
# Проверка всех требований для запуска проекта
# ==========================================

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}🔍 Проверка требований системы...${NC}"
echo ""

ERRORS=0

# Проверка команды
check_command() {
    local cmd=$1
    local name=$2
    
    if command -v $cmd >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name установлен${NC}"
        return 0
    else
        echo -e "${RED}❌ $name НЕ установлен${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Проверка файла
check_file() {
    local file=$1
    local name=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $name существует${NC}"
        return 0
    else
        echo -e "${RED}❌ $name НЕ найден${NC}"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Проверка директории
check_dir() {
    local dir=$1
    local name=$2
    
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ $name существует${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $name отсутствует${NC}"
        return 1
    fi
}

echo -e "${BLUE}📦 Системные утилиты:${NC}"
check_command "python3" "Python 3"
check_command "docker" "Docker"
check_command "docker-compose" "Docker Compose"
check_command "java" "Java"
check_command "allure" "Allure"

echo ""
echo -e "${BLUE}📁 Структура проекта:${NC}"
check_file "docker-compose.yml" "docker-compose.yml"
check_file "requirements.txt" "requirements.txt"
check_file "Makefile" "Makefile"
check_dir "apps/app_with_leak" "apps/app_with_leak"
check_dir "apps/app_without_leak" "apps/app_without_leak"
check_dir "tests" "tests"

echo ""
echo -e "${BLUE}🐍 Python окружение:${NC}"
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
    
    if [ -f "venv/bin/pytest" ]; then
        echo -e "${GREEN}✅ pytest установлен${NC}"
    else
        echo -e "${RED}❌ pytest НЕ установлен${NC}"
        ERRORS=$((ERRORS + 1))
    fi
    
    if [ -f "venv/bin/allure" ] || command -v allure >/dev/null 2>&1; then
        echo -e "${GREEN}✅ allure доступен${NC}"
    else
        echo -e "${RED}❌ allure НЕ доступен${NC}"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}❌ Виртуальное окружение НЕ создано${NC}"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo -e "${BLUE}🐳 Docker:${NC}"
if docker ps >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker daemon работает${NC}"
else
    echo -e "${RED}❌ Docker daemon НЕ работает${NC}"
    ERRORS=$((ERRORS + 1))
fi

if groups $USER | grep -q docker; then
    echo -e "${GREEN}✅ Пользователь в группе docker${NC}"
else
    echo -e "${YELLOW}⚠️  Пользователь НЕ в группе docker${NC}"
    echo -e "${YELLOW}   Выполните: sudo usermod -aG docker \$USER${NC}"
fi

echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Все проверки пройдены!${NC}"
    echo -e "${GREEN}Можно запускать: make full-demo${NC}"
    exit 0
else
    echo -e "${RED}❌ Найдено ошибок: $ERRORS${NC}"
    echo -e "${YELLOW}Запустите: make install${NC}"
    exit 1
fi
