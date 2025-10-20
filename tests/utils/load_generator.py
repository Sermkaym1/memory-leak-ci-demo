"""
Генератор нагрузки для тестирования приложений
"""
import requests
import threading
import time
import random
from typing import List, Dict
from queue import Queue


class LoadGenerator:
    """
    Генератор HTTP нагрузки на приложение
    """
    
    def __init__(self, base_url: str):
        """
        Args:
            base_url: Базовый URL приложения (например, http://localhost:5000)
        """
        self.base_url = base_url
        self.stop_flag = False
        self.threads = []
        self.results_queue = Queue()
        
        # Статистика
        self.stats = {
            'total_requests': 0,
            'successful': 0,
            'errors': 0,
            'response_times': [],
            'start_time': None,
            'end_time': None
        }
    
    def start(self, endpoints: List[str], rps: int = 5, duration: int = 600):
        """
        Запускает генерацию нагрузки
        
        Args:
            endpoints: Список endpoint'ов для запросов
            rps: Запросов в секунду (requests per second)
            duration: Длительность в секундах
        """
        print(f"🚀 Запуск генератора нагрузки:")
        print(f"   URL: {self.base_url}")
        print(f"   RPS: {rps}")
        print(f"   Длительность: {duration} сек ({duration/60:.1f} мин)")
        print(f"   Endpoints: {endpoints}")
        
        self.stop_flag = False
        self.stats['start_time'] = time.time()
        
        # Запускаем потоки
        for i in range(rps):
            thread = threading.Thread(
                target=self._worker,
                args=(endpoints, duration),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            
            # Небольшая задержка для равномерного распределения запросов
            time.sleep(1.0 / rps)
    
    def _worker(self, endpoints: List[str], duration: int):
        """
        Рабочий поток для генерации запросов
        """
        start_time = time.time()
        
        while not self.stop_flag and (time.time() - start_time < duration):
            try:
                # Выбираем случайный endpoint
                endpoint = random.choice(endpoints)
                url = f"{self.base_url}{endpoint}"
                
                # Генерируем случайные данные
                payload = self._generate_payload(endpoint)
                
                # Выполняем запрос
                request_start = time.time()
                
                if endpoint in ['/api/cache', '/api/file', '/api/redis']:
                    response = requests.post(url, json=payload, timeout=5)
                else:
                    response = requests.get(url, timeout=5)
                
                response_time = time.time() - request_start
                
                # Записываем результат
                self.results_queue.put({
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200
                })
                
                self.stats['total_requests'] += 1
                self.stats['response_times'].append(response_time)
                
                if response.status_code == 200:
                    self.stats['successful'] += 1
                else:
                    self.stats['errors'] += 1
                
            except Exception as e:
                self.stats['total_requests'] += 1
                self.stats['errors'] += 1
                self.results_queue.put({
                    'endpoint': endpoint,
                    'error': str(e),
                    'success': False
                })
            
            # Пауза между запросами (1 секунда для каждого потока)
            time.sleep(1)
    
    def _generate_payload(self, endpoint: str) -> Dict:
        """
        Генерирует payload для POST запросов
        """
        if endpoint == '/api/cache':
            return {
                'key': f'key_{random.randint(1, 1000)}',
                'value': 'x' * random.randint(100, 1000)
            }
        
        elif endpoint == '/api/file':
            return {
                'content': 'test data\n' * random.randint(10, 100)
            }
        
        elif endpoint == '/api/redis':
            return {
                'key': f'redis_key_{random.randint(1, 1000)}',
                'value': 'y' * random.randint(100, 1000)
            }
        
        return {}
    
    def stop(self):
        """
        Останавливает генерацию нагрузки
        """
        print("🛑 Остановка генератора нагрузки...")
        self.stop_flag = True
        self.stats['end_time'] = time.time()
        
        # Ждем завершения всех потоков
        for thread in self.threads:
            thread.join(timeout=5)
        
        print("✅ Генератор нагрузки остановлен")
    
    def get_statistics(self) -> Dict:
        """
        Возвращает статистику выполнения
        """
        if not self.stats['response_times']:
            avg_response_time = 0.0
            min_response_time = 0.0
            max_response_time = 0.0
        else:
            avg_response_time = sum(self.stats['response_times']) / len(self.stats['response_times'])
            min_response_time = min(self.stats['response_times'])
            max_response_time = max(self.stats['response_times'])
        
        total_time = 0
        if self.stats['start_time'] and self.stats['end_time']:
            total_time = self.stats['end_time'] - self.stats['start_time']
        
        return {
            'total_requests': self.stats['total_requests'],
            'successful': self.stats['successful'],
            'errors': self.stats['errors'],
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'total_duration': total_time,
            'actual_rps': self.stats['total_requests'] / total_time if total_time > 0 else 0
        }
