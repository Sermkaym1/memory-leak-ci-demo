"""
Flask приложение с РЕАЛИСТИЧНЫМИ утечками памяти.
Каждая утечка помечена комментариями для обучения.
"""
import os
import time
import psycopg2
from flask import Flask, jsonify, request, Response
from datetime import datetime
import redis

app = Flask(__name__)

# ========================================
# УТЕЧКА #1: Глобальный кеш без очистки
# ========================================
# Проблема: словарь растет бесконечно, никогда не очищается
# В продакшене: использовать Redis с TTL или LRU cache
GLOBAL_CACHE = {}
REQUEST_HISTORY = []  # тоже утечка - список растет

# ========================================
# УТЕЧКА #2: Пул соединений к БД
# ========================================
# Проблема: соединения создаются, но не закрываются
DB_CONNECTIONS = []  # утечка - список открытых соединений

# ========================================
# УТЕЧКА #3: Файловые дескрипторы
# ========================================
OPEN_FILES = []  # утечка - файлы не закрываются


@app.route('/health')
def health():
    """Healthcheck endpoint"""
    return jsonify({"status": "ok", "leaky": True})


@app.route('/api/cache', methods=['POST'])
def cache_data():
    """
    УТЕЧКА #1 ДЕМОНСТРАЦИЯ
    Сохраняет данные в кеш БЕЗ очистки старых записей
    """
    data = request.json
    key = data.get('key', f'key_{len(GLOBAL_CACHE)}')
    
    # ❌ УТЕЧКА: Данные накапливаются без лимита
    # Правильно: использовать LRU cache или TTL
    GLOBAL_CACHE[key] = {
        'data': data.get('value', 'x' * 1000),  # 1KB данных
        'timestamp': datetime.now(),
        'metadata': 'x' * 5000  # Еще 5KB мусора
    }
    
    # ❌ УТЕЧКА: История запросов растет бесконечно
    REQUEST_HISTORY.append({
        'key': key,
        'time': datetime.now(),
        'size': len(str(data))
    })
    
    return jsonify({
        "cached": key,
        "total_cached": len(GLOBAL_CACHE),
        "history_size": len(REQUEST_HISTORY)
    })


@app.route('/api/database', methods=['GET'])
def database_query():
    """
    УТЕЧКА #2 ДЕМОНСТРАЦИЯ
    Создает подключение к БД БЕЗ закрытия
    """
    try:
        # ❌ УТЕЧКА: Соединение создается, но не закрывается
        # Правильно: использовать context manager (with) или connection pool
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'postgres'),
            database=os.getenv('DB_NAME', 'testdb'),
            user=os.getenv('DB_USER', 'testuser'),
            password=os.getenv('DB_PASSWORD', 'testpass')
        )
        
        # ❌ УТЕЧКА: Сохраняем соединение в глобальный список
        DB_CONNECTIONS.append(conn)
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
        cursor.close()
        # conn.close() <- НЕ закрываем специально!
        
        return jsonify({
            "db_version": result[0],
            "open_connections": len(DB_CONNECTIONS),
            "warning": "Connection not closed - MEMORY LEAK!"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file', methods=['POST'])
def write_file():
    """
    УТЕЧКА #3 ДЕМОНСТРАЦИЯ
    Открывает файлы БЕЗ закрытия
    """
    data = request.json
    filename = f"/tmp/leak_{len(OPEN_FILES)}.txt"
    
    # ❌ УТЕЧКА: Файл открывается, но не закрывается
    # Правильно: использовать with open(...) as f:
    f = open(filename, 'w')
    f.write(data.get('content', 'test data\n' * 100))
    f.flush()
    # f.close() <- НЕ закрываем специально!
    
    # ❌ УТЕЧКА: Сохраняем файловые дескрипторы
    OPEN_FILES.append(f)
    
    return jsonify({
        "file": filename,
        "open_files": len(OPEN_FILES),
        "warning": "File descriptor not closed - MEMORY LEAK!"
    })


@app.route('/api/redis', methods=['POST'])
def redis_cache():
    """
    УТЕЧКА #4 ДЕМОНСТРАЦИЯ
    Redis клиент БЕЗ закрытия connection pool
    """
    try:
        data = request.json
        
        # ❌ УТЕЧКА: Каждый раз создаем новый клиент
        # Правильно: переиспользовать один Redis client
        r = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=6379,
            decode_responses=True
        )
        
        key = data.get('key', f'redis_key_{time.time()}')
        value = data.get('value', 'x' * 10000)  # 10KB
        
        r.set(key, value)
        result = r.get(key)
        
        # НЕ закрываем connection pool!
        
        return jsonify({
            "redis_key": key,
            "value_length": len(result),
            "warning": "Redis connection pool not closed!"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/stress')
def stress_test():
    """
    Комбинированный endpoint для стресс-теста
    Вызывает ВСЕ утечки одновременно
    """
    results = []
    
    # Утечка кеша
    for i in range(10):
        GLOBAL_CACHE[f'stress_{i}'] = 'x' * 10000
    results.append(f"Cache size: {len(GLOBAL_CACHE)}")
    
    # Утечка БД соединений
    try:
        for i in range(3):
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'postgres'),
                database=os.getenv('DB_NAME', 'testdb'),
                user=os.getenv('DB_USER', 'testuser'),
                password=os.getenv('DB_PASSWORD', 'testpass')
            )
            DB_CONNECTIONS.append(conn)
        results.append(f"DB connections: {len(DB_CONNECTIONS)}")
    except:
        results.append("DB connection failed")
    
    # Утечка файлов
    for i in range(5):
        f = open(f'/tmp/stress_{i}.txt', 'w')
        f.write('leak' * 1000)
        OPEN_FILES.append(f)
    results.append(f"Open files: {len(OPEN_FILES)}")
    
    return jsonify({
        "results": results,
        "total_memory_leaks": "ALL ACTIVE!"
    })


@app.route('/metrics')
def metrics():
    """Endpoint для Prometheus"""
    metrics_text = f"""# HELP memory_cache_size Size of in-memory cache
# TYPE memory_cache_size gauge
memory_cache_size {len(GLOBAL_CACHE)}

# HELP db_connections_open Number of open database connections
# TYPE db_connections_open gauge
db_connections_open {len(DB_CONNECTIONS)}

# HELP file_descriptors_open Number of open file descriptors
# TYPE file_descriptors_open gauge
file_descriptors_open {len(OPEN_FILES)}

# HELP request_history_size Size of request history
# TYPE request_history_size gauge
request_history_size {len(REQUEST_HISTORY)}
"""
    return Response(metrics_text, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
