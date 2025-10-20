"""
Веб-дашборд для мониторинга тестов в реальном времени
Использует Flask + WebSocket для live обновлений
"""
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import json
import time
import threading
from datetime import datetime
from typing import Dict, List
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'memory-leak-dashboard-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Глобальное состояние дашборда
dashboard_state = {
    "current_test": None,
    "test_progress": 0,
    "memory_data": [],
    "active_containers": [],
    "test_results": [],
    "system_status": "idle"
}


class LiveDashboard:
    """
    Живой дашборд для мониторинга тестов
    """
    
    def __init__(self):
        self.is_running = False
        self.current_test_thread = None
    
    def start_test_monitoring(self, test_name: str, duration_minutes: int):
        """Запускает мониторинг теста"""
        global dashboard_state
        
        dashboard_state.update({
            "current_test": test_name,
            "test_progress": 0,
            "memory_data": [],
            "system_status": "running"
        })
        
        # Уведомляем всех подключенных клиентов
        socketio.emit('test_started', {
            'test_name': test_name,
            'duration_minutes': duration_minutes,
            'timestamp': datetime.now().isoformat()
        })
        
        # Запускаем поток мониторинга
        self.is_running = True
        self.current_test_thread = threading.Thread(
            target=self._monitor_test_loop, 
            args=(test_name, duration_minutes)
        )
        self.current_test_thread.start()
    
    def _monitor_test_loop(self, test_name: str, duration_minutes: int):
        """Цикл мониторинга теста"""
        start_time = time.time()
        duration_seconds = duration_minutes * 60
        
        while self.is_running and (time.time() - start_time) < duration_seconds:
            elapsed = time.time() - start_time
            progress = (elapsed / duration_seconds) * 100
            
            # Имитируем данные памяти (в реальности берем из EnhancedMemoryMonitor)
            fake_memory = {
                'timestamp': time.time(),
                'rss_mb': 50 + (elapsed / 60) * 5,  # Рост 5 MB/мин
                'vms_mb': 200 + (elapsed / 60) * 3,
                'cpu_percent': 15 + (elapsed % 30) / 3,
                'connections': int(10 + elapsed / 30),
                'open_files': int(20 + elapsed / 20)
            }
            
            # Обновляем состояние
            dashboard_state["test_progress"] = progress
            dashboard_state["memory_data"].append(fake_memory)
            
            # Отправляем обновление клиентам
            socketio.emit('test_update', {
                'test_name': test_name,
                'progress': progress,
                'elapsed_minutes': elapsed / 60,
                'remaining_minutes': (duration_seconds - elapsed) / 60,
                'memory_data': fake_memory
            })
            
            time.sleep(5)  # Обновления каждые 5 секунд
        
        # Тест завершен
        self._finish_test(test_name)
    
    def _finish_test(self, test_name: str):
        """Завершает мониторинг теста"""
        global dashboard_state
        
        self.is_running = False
        
        # Анализируем результаты
        memory_data = dashboard_state["memory_data"]
        if memory_data:
            initial_memory = memory_data[0]['rss_mb']
            final_memory = memory_data[-1]['rss_mb']
            memory_growth = final_memory - initial_memory
            
            # Определяем утечку
            has_leak = memory_growth > 20  # Простой критерий
            
            result = {
                'test_name': test_name,
                'status': 'failed' if has_leak else 'passed',
                'memory_growth_mb': memory_growth,
                'has_leak': has_leak,
                'duration_minutes': len(memory_data) * 5 / 60,
                'timestamp': datetime.now().isoformat()
            }
            
            dashboard_state["test_results"].append(result)
            dashboard_state["system_status"] = "completed"
            
            # Уведомляем клиентов о завершении
            socketio.emit('test_completed', result)
    
    def stop_test(self):
        """Останавливает текущий тест"""
        self.is_running = False
        if self.current_test_thread:
            self.current_test_thread.join(timeout=5)
        
        dashboard_state["system_status"] = "stopped"
        socketio.emit('test_stopped', {'timestamp': datetime.now().isoformat()})


# Глобальный экземпляр дашборда
live_dashboard = LiveDashboard()


# ==========================================
# Flask Routes
# ==========================================

@app.route('/')
def index():
    """Главная страница дашборда"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """API: Текущий статус системы"""
    return jsonify(dashboard_state)

@app.route('/api/start_test/<test_name>/<int:duration>')
def start_test(test_name: str, duration: int):
    """API: Запуск теста"""
    if dashboard_state["system_status"] == "running":
        return jsonify({"error": "Тест уже запущен"}), 400
    
    live_dashboard.start_test_monitoring(test_name, duration)
    return jsonify({"message": f"Тест {test_name} запущен на {duration} минут"})

@app.route('/api/stop_test')
def stop_test():
    """API: Остановка теста"""
    live_dashboard.stop_test()
    return jsonify({"message": "Тест остановлен"})

@app.route('/api/results')
def get_results():
    """API: История результатов тестов"""
    return jsonify(dashboard_state["test_results"])


# ==========================================
# WebSocket Events
# ==========================================

@socketio.on('connect')
def handle_connect():
    """Клиент подключился"""
    print(f"📱 Клиент подключился: {datetime.now()}")
    emit('connected', {
        'message': 'Подключение к Memory Leak Dashboard установлено',
        'current_state': dashboard_state
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Клиент отключился"""
    print(f"📱 Клиент отключился: {datetime.now()}")

@socketio.on('request_status')
def handle_status_request():
    """Клиент запросил текущий статус"""
    emit('status_update', dashboard_state)


# ==========================================
# HTML Template
# ==========================================

def create_dashboard_template():
    """Создает HTML шаблон дашборда"""
    
    template_dir = "templates"
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    html_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔍 Memory Leak Detection Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status-card {
            text-align: center;
        }
        .status-running { border-left: 5px solid #4CAF50; }
        .status-idle { border-left: 5px solid #9E9E9E; }
        .status-failed { border-left: 5px solid #F44336; }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            transition: width 0.3s ease;
        }
        
        .metric {
            display: inline-block;
            margin: 10px;
            padding: 10px 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 3px solid #007bff;
        }
        
        .control-buttons {
            text-align: center;
            margin: 20px 0;
        }
        .btn {
            padding: 10px 20px;
            margin: 0 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .btn-start { background: #4CAF50; color: white; }
        .btn-stop { background: #F44336; color: white; }
        .btn:hover { opacity: 0.8; }
        
        .log-container {
            background: #263238;
            color: #4CAF50;
            font-family: 'Courier New', monospace;
            padding: 15px;
            border-radius: 5px;
            height: 200px;
            overflow-y: auto;
            font-size: 12px;
        }
        
        #memory-chart {
            width: 100%;
            height: 300px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Memory Leak Detection Dashboard</h1>
        <p>Мониторинг тестов в реальном времени</p>
    </div>
    
    <div class="dashboard-grid">
        <div class="card status-card" id="status-card">
            <h3>📊 Статус системы</h3>
            <div id="system-status">Загрузка...</div>
            <div id="current-test"></div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
            </div>
            <div id="progress-text">0%</div>
        </div>
        
        <div class="card">
            <h3>🎮 Управление</h3>
            <div class="control-buttons">
                <button class="btn btn-start" onclick="startTest()">▶️ Запустить быстрый тест</button>
                <button class="btn btn-stop" onclick="stopTest()">⏹️ Остановить</button>
            </div>
            <div id="controls-status">Готов к запуску</div>
        </div>
    </div>
    
    <div class="dashboard-grid">
        <div class="card">
            <h3>📈 Метрики памяти</h3>
            <div id="memory-metrics">
                <div class="metric">RSS: <span id="rss-memory">0</span> MB</div>
                <div class="metric">VMS: <span id="vms-memory">0</span> MB</div>
                <div class="metric">CPU: <span id="cpu-usage">0</span>%</div>
                <div class="metric">Соединения: <span id="connections">0</span></div>
            </div>
        </div>
        
        <div class="card">
            <h3>📋 Последние результаты</h3>
            <div id="test-results">Нет результатов</div>
        </div>
    </div>
    
    <div class="card">
        <h3>📊 График памяти</h3>
        <canvas id="memory-chart"></canvas>
    </div>
    
    <div class="card">
        <h3>📝 Лог событий</h3>
        <div class="log-container" id="log-container"></div>
    </div>

    <script>
        // WebSocket подключение
        const socket = io();
        
        // График памяти
        const ctx = document.getElementById('memory-chart').getContext('2d');
        const memoryChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'RSS Memory (MB)',
                    data: [],
                    borderColor: '#F44336',
                    tension: 0.1
                }, {
                    label: 'VMS Memory (MB)', 
                    data: [],
                    borderColor: '#2196F3',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        // Функции управления
        function startTest() {
            fetch('/api/start_test/quick_demo/5')
                .then(response => response.json())
                .then(data => addLog('🚀 ' + data.message));
        }
        
        function stopTest() {
            fetch('/api/stop_test')
                .then(response => response.json())
                .then(data => addLog('⏹️ ' + data.message));
        }
        
        function addLog(message) {
            const logContainer = document.getElementById('log-container');
            const timestamp = new Date().toLocaleTimeString();
            logContainer.innerHTML += `[${timestamp}] ${message}\\n`;
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        function updateStatus(status) {
            const statusCard = document.getElementById('status-card');
            const systemStatus = document.getElementById('system-status');
            
            statusCard.className = `card status-card status-${status}`;
            systemStatus.textContent = status === 'running' ? '🔄 Тест выполняется' : 
                                      status === 'completed' ? '✅ Завершено' : '⏸️ Ожидание';
        }
        
        // WebSocket события
        socket.on('connected', function(data) {
            addLog('📱 Подключение установлено');
            updateStatus(data.current_state.system_status);
        });
        
        socket.on('test_started', function(data) {
            addLog(`🧪 Запущен тест: ${data.test_name} (${data.duration_minutes} мин)`);
            updateStatus('running');
            document.getElementById('current-test').textContent = data.test_name;
        });
        
        socket.on('test_update', function(data) {
            // Обновляем прогресс
            const progressFill = document.getElementById('progress-fill');
            const progressText = document.getElementById('progress-text');
            progressFill.style.width = data.progress + '%';
            progressText.textContent = Math.round(data.progress) + '%';
            
            // Обновляем метрики
            document.getElementById('rss-memory').textContent = data.memory_data.rss_mb.toFixed(1);
            document.getElementById('vms-memory').textContent = data.memory_data.vms_mb.toFixed(1);
            document.getElementById('cpu-usage').textContent = data.memory_data.cpu_percent.toFixed(1);
            document.getElementById('connections').textContent = data.memory_data.connections;
            
            // Обновляем график
            const timestamp = new Date(data.memory_data.timestamp * 1000).toLocaleTimeString();
            memoryChart.data.labels.push(timestamp);
            memoryChart.data.datasets[0].data.push(data.memory_data.rss_mb);
            memoryChart.data.datasets[1].data.push(data.memory_data.vms_mb);
            
            // Ограничиваем количество точек на графике
            if (memoryChart.data.labels.length > 50) {
                memoryChart.data.labels.shift();
                memoryChart.data.datasets[0].data.shift();
                memoryChart.data.datasets[1].data.shift();
            }
            
            memoryChart.update('none');
        });
        
        socket.on('test_completed', function(data) {
            const status = data.has_leak ? 'УТЕЧКА ОБНАРУЖЕНА' : 'OK';
            const emoji = data.has_leak ? '🔴' : '✅';
            addLog(`${emoji} Тест завершен: ${data.test_name} - ${status} (${data.memory_growth_mb.toFixed(1)} MB)`);
            updateStatus('completed');
            
            // Обновляем результаты
            const resultsDiv = document.getElementById('test-results');
            resultsDiv.innerHTML = `
                <div style="padding: 10px; background: ${data.has_leak ? '#ffebee' : '#e8f5e8'}; border-radius: 5px;">
                    ${emoji} <strong>${data.test_name}</strong><br>
                    Рост памяти: ${data.memory_growth_mb.toFixed(1)} MB<br>
                    Статус: ${status}
                </div>
            `;
        });
        
        // Инициализация
        addLog('🔍 Memory Leak Dashboard запущен');
    </script>
</body>
</html>'''
    
    with open(os.path.join(template_dir, 'dashboard.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ HTML шаблон дашборда создан")


if __name__ == '__main__':
    # Создаем шаблон
    create_dashboard_template()
    
    print("🚀 Запуск Memory Leak Dashboard...")
    print("📱 Откройте http://localhost:5555 в браузере")
    
    # Запускаем Flask приложение
    socketio.run(app, host='0.0.0.0', port=5555, debug=True)