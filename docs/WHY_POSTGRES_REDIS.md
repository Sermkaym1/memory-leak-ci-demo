# 🤔 Зачем нужны PostgreSQL и Redis?

## 📋 **Краткий ответ:**

PostgreSQL и Redis нужны для **создания РЕАЛИСТИЧНЫХ утечек памяти**, которые часто встречаются в реальных приложениях.

---

## 🎯 **Подробное объяснение:**

### 1. **PostgreSQL - для утечек DB соединений**

**Проблема в реальном мире:**
```python
# ❌ Плохой код (УТЕЧКА)
def get_user_data():
    conn = psycopg2.connect("postgresql://...")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    # ЗАБЫЛИ ЗАКРЫТЬ: conn.close()
    return data
```

**Что происходит:**
- При каждом запросе создается новое соединение с БД
- Соединения НЕ закрываются (`conn.close()` забыли)
- Накапливаются открытые TCP соединения
- Память растет, БД может отказать в новых соединениях

**Как это проявляется в нашем проекте:**
```python
# apps/app_with_leak/app.py - строка 78
@app.route('/api/database')
def database_query():
    # ❌ УТЕЧКА: Соединение создается, но не закрывается
    conn = psycopg2.connect(...)
    DB_CONNECTIONS.append(conn)  # Накапливаем в списке
    # conn.close() <- НЕ закрываем специально!
```

**Правильный способ:**
```python
# apps/app_without_leak/app.py
# ✅ Connection Pool - переиспользуем соединения
DB_POOL = psycopg2.pool.SimpleConnectionPool(minconn=1, maxconn=10, ...)

def database_query():
    conn = DB_POOL.getconn()  # Берем из пула
    try:
        # используем соединение
        pass
    finally:
        DB_POOL.putconn(conn)  # Возвращаем в пул
```

---

### 2. **Redis - для утечек connection pool**

**Проблема в реальном мире:**
```python
# ❌ Плохой код (УТЕЧКА)
def cache_data(key, value):
    # Каждый раз создаем НОВЫЙ клиент
    redis_client = redis.Redis(host='redis')
    redis_client.set(key, value)
    # НЕ закрываем connection pool!
```

**Что происходит:**
- Redis клиент создает внутренний connection pool
- При создании нового клиента каждый раз - пул НЕ закрывается
- Накапливаются TCP соединения к Redis
- Память и файловые дескрипторы растут

**Как это проявляется в нашем проекте:**
```python
# apps/app_with_leak/app.py - строка 123
@app.route('/api/redis')
def redis_cache():
    # ❌ УТЕЧКА: Каждый раз создаем новый клиент
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'))
    # НЕ закрываем connection pool!
```

**Правильный способ:**
```python
# apps/app_without_leak/app.py
# ✅ Singleton client - переиспользуем один клиент
REDIS_CLIENT = None

def get_redis_client():
    global REDIS_CLIENT
    if REDIS_CLIENT is None:
        REDIS_CLIENT = redis.Redis(
            connection_pool=redis.ConnectionPool(max_connections=10)
        )
    return REDIS_CLIENT
```

---

## 🧪 **Как это влияет на тесты:**

### **Тест приложения С утечкой:**
1. Генерируем запросы к `/api/database` и `/api/redis`
2. Каждый запрос создает новые соединения
3. Соединения НЕ закрываются
4. Память растет постоянно → **УТЕЧКА ОБНАРУЖЕНА** ✅

### **Тест приложения БЕЗ утечки:**
1. Те же запросы к БД и Redis
2. Используются connection pools
3. Соединения переиспользуются
4. Память стабильна → **Утечки НЕТ** ✅

---

## 💡 **Можно ли без них?**

**Технически - ДА**, но тогда:

❌ **Утечки будут искусственными:**
```python
# Просто создаем много объектов в памяти
big_list = []
for i in range(10000):
    big_list.append("x" * 1000)  # Накапливаем строки
```

✅ **С PostgreSQL + Redis утечки РЕАЛИСТИЧНЫЕ:**
- Такие ошибки действительно происходят в продакшене
- Показывают правильные паттерны исправления
- Тесты применимы к реальным проектам

---

## 🚀 **Резюме:**

| Компонент | Зачем нужен | Какую утечку демонстрирует |
|-----------|-------------|----------------------------|
| **PostgreSQL** | Реалистичные DB запросы | Незакрытые соединения к БД |
| **Redis** | Кеширование данных | Connection pool утечки |
| **Flask App** | HTTP API endpoints | Комбинация всех утечек |

**Итог:** PostgreSQL и Redis делают демо **максимально приближенным к реальности** и показывают частые ошибки в production-коде.