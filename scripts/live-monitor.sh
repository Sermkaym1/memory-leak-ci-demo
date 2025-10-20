#!/bin/bash

# ==========================================
# Живой мониторинг памяти контейнеров
# ==========================================

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       Живой мониторинг памяти контейнеров                 ║${NC}"
echo -e "${GREEN}║       (Нажмите Ctrl+C для выхода)                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Функция для получения памяти контейнера
get_memory() {
    local container=$1
    local stats=$(docker stats --no-stream --format "{{.MemUsage}}" $container 2>/dev/null)
    echo "$stats"
}

# Функция для получения CPU
get_cpu() {
    local container=$1
    local stats=$(docker stats --no-stream --format "{{.CPUPerc}}" $container 2>/dev/null)
    echo "$stats"
}

# Главный цикл мониторинга
while true; do
    clear
    
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  $(date '+%Y-%m-%d %H:%M:%S')                                      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # App with leak
    if docker ps --format '{{.Names}}' | grep -q "app-with-leak"; then
        mem_leak=$(get_memory "app-with-leak")
        cpu_leak=$(get_cpu "app-with-leak")
        echo -e "${RED}🔴 App WITH Leak:${NC}"
        echo -e "   Memory: ${YELLOW}$mem_leak${NC}"
        echo -e "   CPU:    ${YELLOW}$cpu_leak${NC}"
    else
        echo -e "${RED}🔴 App WITH Leak: НЕ ЗАПУЩЕН${NC}"
    fi
    
    echo ""
    
    # App without leak
    if docker ps --format '{{.Names}}' | grep -q "app-without-leak"; then
        mem_no_leak=$(get_memory "app-without-leak")
        cpu_no_leak=$(get_cpu "app-without-leak")
        echo -e "${GREEN}🟢 App WITHOUT Leak:${NC}"
        echo -e "   Memory: ${YELLOW}$mem_no_leak${NC}"
        echo -e "   CPU:    ${YELLOW}$cpu_no_leak${NC}"
    else
        echo -e "${GREEN}🟢 App WITHOUT Leak: НЕ ЗАПУЩЕН${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
    
    # PostgreSQL
    if docker ps --format '{{.Names}}' | grep -q "postgres-leak-demo"; then
        mem_pg=$(get_memory "postgres-leak-demo")
        echo -e "🗄️  PostgreSQL:   Memory: ${YELLOW}$mem_pg${NC}"
    fi
    
    # Redis
    if docker ps --format '{{.Names}}' | grep -q "redis-leak-demo"; then
        mem_redis=$(get_memory "redis-leak-demo")
        echo -e "🔴 Redis:         Memory: ${YELLOW}$mem_redis${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Обновление каждые 5 секунд...${NC}"
    
    sleep 5
done
