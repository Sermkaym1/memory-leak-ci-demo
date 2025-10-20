"""
Flask приложение БЕЗ утечек памяти.
Показывает ПРАВИЛЬНЫЕ паттерны работы с ресурсами.
"""
import os
import psycopg2
from psycopg2 import pool
from flask import Flask, jsonify, request, Response
from datetime import datetime
import redis
from functools import lru_cache
from cachetools import TTLCache
import atexit

app = Flask(__name__)

# ========================================
# ✅ ПРАВИЛЬНО: Cache с лимитом и TTL
# ========================================
# Использует cachetools с максимальным размером и временем жизни
CACHE = TTLCache(maxsize=100, ttl=300)  # 100 элементов, 5 минут TTL

# ========================================
# ✅ ПРАВИЛЬНО: Connection Pool для БД
# ========================================
# Переиспользуем соединения вместо создания новых
DB_POOL = None

def init_db_pool():
    global DB_POOL
    DB_POOL = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=os.getenv('DB_HOST', 'postgres'),
        database=os.getenv('DB_NAME', 'testdb'),
        user=os.getenv('DB_USER', 'testuser'),
        password=os.getenv('DB_PASSWORD', 'testpass')
    )

def close_db_pool():
    if DB_POOL:
        DB_POOL.closeall()

# ========================================
# ✅ ПРАВИЛЬНО: Singleton Redis client
# ========================================
REDIS_CLIENT = None

def get_redis_client():
    global REDIS_CLIENT
    if REDIS_CLIENT is None:
        REDIS_CLIENT = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=6379,
            decode_responses=True,
            connection_pool=redis.ConnectionPool(max_connections=10)
        )
    return REDIS_CLIENT

# Закрываем ресурсы при остановке
atexit.register(close_db_pool)


@app.route('/health')
def health():
    """Healthcheck endpoint"""
    return jsonify({"status": "ok", "leaky": False})


@app.route('/api/cache', methods=['POST'])
def cache_data():
    """
    ✅ ПРАВИЛЬНО: Cache с автоочисткой
    """
    data = request.json
    key = data.get('key', f'key_{len(CACHE)}')
    
    # ✅ TTLCache автоматически удаляет старые записи
    CACHE[key] = {
        'data': data.get('value', 'x' * 1000),
        'timestamp': datetime.now()
    }
    
    return jsonify({
        "cached": key,
        "total_cached": len(CACHE),
        "max_size": CACHE.maxsize,
        "ttl": CACHE.ttl
    })


@app.route('/api/database', methods=['GET'])
def database_query():
    """
    ✅ ПРАВИЛЬНО: Использование connection pool
    """
    if DB_POOL is None:
        init_db_pool()
    
    conn = None
    try:
        # ✅ Берем соединение из пула
        conn = DB_POOL.getconn()
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
        cursor.close()
        
        return jsonify({
            "db_version": result[0],
            "pool_size": DB_POOL.maxconn,
            "info": "Using connection pool - NO LEAK!"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        # ✅ ВАЖНО: Возвращаем соединение в пул
        if conn:
            DB_POOL.putconn(conn)


@app.route('/api/file', methods=['POST'])
def write_file():
    """
    ✅ ПРАВИЛЬНО: Context manager для файлов
    """
    data = request.json
    filename = f"/tmp/noleak_{datetime.now().timestamp()}.txt"
    
    # ✅ Context manager автоматически закрывает файл
    with open(filename, 'w') as f:
        f.write(data.get('content', 'test data\n' * 100))
    
    return jsonify({
        "file": filename,
        "info": "File properly closed - NO LEAK!"
    })


@app.route('/api/redis', methods=['POST'])
def redis_cache():
    """
    ✅ ПРАВИЛЬНО: Переиспользуем Redis client
    """
    try:
        data = request.json
        
        # ✅ Используем singleton client с connection pool
        r = get_redis_client()
        
        key = data.get('key', f'redis_key_{datetime.now().timestamp()}')
        value = data.get('value', 'x' * 10000)
        
        # ✅ Устанавливаем TTL для ключа
        r.setex(key, 300, value)  # 5 минут TTL
        result = r.get(key)
        
        return jsonify({
            "redis_key": key,
            "value_length": len(result) if result else 0,
            "ttl": r.ttl(key),
            "info": "Using connection pool with TTL - NO LEAK!"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/stress')
def stress_test():
    """
    Комбинированный endpoint - все ресурсы управляются правильно
    """
    results = []
    
    # Cache с автоочисткой
    for i in range(10):
        CACHE[f'stress_{i}'] = 'x' * 10000
    results.append(f"Cache size: {len(CACHE)}/{CACHE.maxsize}")
    
    # DB Connection pool
    if DB_POOL is None:
        init_db_pool()
    
    try:
        for i in range(3):
            conn = DB_POOL.getconn()
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.close()
            DB_POOL.putconn(conn)
        results.append(f"DB pool: {DB_POOL.maxconn} connections")
    except:
        results.append("DB connection failed")
    
    # Файлы с context manager
    for i in range(5):
        with open(f'/tmp/stress_noleak_{i}.txt', 'w') as f:
            f.write('no leak' * 1000)
    results.append("Files: properly closed")
    
    return jsonify({
        "results": results,
        "memory_management": "EXCELLENT - NO LEAKS!"
    })


@app.route('/metrics')
def metrics():
    """Endpoint для Prometheus"""
    metrics_text = f"""# HELP memory_cache_size Size of in-memory cache
# TYPE memory_cache_size gauge
memory_cache_size {len(CACHE)}

# HELP memory_cache_max Maximum cache size
# TYPE memory_cache_max gauge
memory_cache_max {CACHE.maxsize}
"""
    return Response(metrics_text, mimetype='text/plain')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
