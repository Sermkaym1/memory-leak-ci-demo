"""
Утилита для мониторинга памяти Docker контейнеров
"""
import subprocess
import time
from typing import Dict
import re


class MemoryMonitor:
    """
    Мониторинг потребления памяти Docker контейнером
    Использует docker stats через subprocess для надёжности
    """
    
    def __init__(self, container):
        """
        Args:
            container: Docker container объект
        """
        self.container = container
        self.container_name = container.name
        print(f"✅ MemoryMonitor инициализирован для контейнера: {self.container_name}")
    
    def get_current_memory(self) -> Dict[str, float]:
        """
        Получает текущее потребление памяти контейнером
        
        Returns:
            dict: {
                'rss_mb': float,
                'vms_mb': float,
                'percent': float,
                'timestamp': float
            }
        """
        try:
            # Используем docker stats через subprocess
            result = subprocess.run(
                ['docker', 'stats', self.container_name, '--no-stream', 
                 '--format', '{{.MemUsage}}\t{{.CPUPerc}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"⚠️  docker stats ошибка: {result.stderr}")
                return self._default_memory()
            
            output = result.stdout.strip()
            
            if not output:
                print(f"⚠️  docker stats пустой вывод")
                return self._default_memory()
            
            parts = output.split('\t')
            if len(parts) < 2:
                print(f"⚠️  Неожиданный формат: {output}")
                return self._default_memory()
            
            mem_usage = parts[0]
            cpu_perc = parts[1]
            
            if '/' not in mem_usage:
                print(f"⚠️  Неожиданный формат памяти: {mem_usage}")
                return self._default_memory()
            
            usage_str, limit_str = mem_usage.split('/')
            
            usage_mb = self._parse_memory(usage_str.strip())
            limit_mb = self._parse_memory(limit_str.strip())
            cpu_percent = float(cpu_perc.replace('%', '').strip())
            
            return {
                'rss_mb': usage_mb,
                'usage_mb': usage_mb,
                'limit_mb': limit_mb,
                'vms_mb': usage_mb,
                'percent': cpu_percent,
                'timestamp': time.time()
            }
            
        except subprocess.TimeoutExpired:
            print(f"⚠️  docker stats таймаут")
            return self._default_memory()
            
        except Exception as e:
            print(f"⚠️  Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return self._default_memory()
    
    def _parse_memory(self, mem_str: str) -> float:
        """Парсит строку памяти в MB"""
        mem_str = mem_str.strip()
        
        match = re.match(r'([\d.]+)\s*([a-zA-Z]+)', mem_str)
        if not match:
            print(f"⚠️  Не могу распарсить: {mem_str}")
            return 0.0
        
        value = float(match.group(1))
        unit = match.group(2).upper()
        
        if unit in ['MIB', 'MB', 'M']:
            return value
        elif unit in ['GIB', 'GB', 'G']:
            return value * 1024
        elif unit in ['KIB', 'KB', 'K']:
            return value / 1024
        elif unit in ['B', 'BYTES']:
            return value / (1024 * 1024)
        else:
            return value
    
    def _default_memory(self):
        """Значения по умолчанию"""
        return {
            'rss_mb': 0.0,
            'usage_mb': 0.0,
            'limit_mb': 512.0,
            'vms_mb': 0.0,
            'percent': 0.0,
            'timestamp': time.time()
        }
    
    def get_memory_trend(self, measurements: list) -> str:
        """Определяет тренд"""
        if len(measurements) < 3:
            return 'insufficient_data'
        
        quarter = max(1, len(measurements) // 4)
        
        first_quarter_avg = sum(m['rss_mb'] for m in measurements[:quarter]) / quarter
        last_quarter_avg = sum(m['rss_mb'] for m in measurements[-quarter:]) / quarter
        
        diff = last_quarter_avg - first_quarter_avg
        
        if diff > 10:
            return 'increasing'
        elif diff < -10:
            return 'decreasing'
        else:
            return 'stable'
    
    def calculate_growth_rate(self, measurements: list) -> float:
        """Вычисляет скорость роста"""
        if len(measurements) < 2:
            return 0.0
        
        first = measurements[0]
        last = measurements[-1]
        
        memory_diff = last['rss_mb'] - first['rss_mb']
        time_diff = (last['timestamp'] - first['timestamp']) / 60
        
        if time_diff == 0:
            return 0.0
        
        return memory_diff / time_diff
    
    def get_container_logs(self, tail: int = 100) -> str:
        """Получает логи"""
        try:
            result = subprocess.run(
                ['docker', 'logs', '--tail', str(tail), self.container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except Exception as e:
            return f"Ошибка: {e}"
