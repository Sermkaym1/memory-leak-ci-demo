"""
Расширенный мониторинг памяти с дополнительными метриками
Добавляет мониторинг системных ресурсов, сетевых соединений, файловых дескрипторов
"""
import psutil
import docker
import time
import json
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemMetrics:
    """Системные метрики контейнера"""
    timestamp: float
    # Память
    rss_mb: float
    vms_mb: float
    memory_percent: float
    # CPU
    cpu_percent: float
    # Сеть
    network_connections: int
    tcp_connections: int
    # Файлы
    open_files: int
    # Дополнительно
    threads_count: int
    context_switches: int


class EnhancedMemoryMonitor:
    """
    Расширенный мониторинг памяти с детальными метриками
    """
    
    def __init__(self, container):
        self.container = container
        self.container_name = container.name
        self.client = docker.from_env()
        self.metrics_history: List[SystemMetrics] = []
        print(f"✅ EnhancedMemoryMonitor для {self.container_name}")
    
    def get_detailed_metrics(self) -> SystemMetrics:
        """
        Получает детальные метрики контейнера
        """
        try:
            # Получаем статистику Docker контейнера
            stats = self.container.stats(stream=False)
            
            # Парсим память
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100
            
            rss_mb = memory_usage / (1024 * 1024)
            vms_mb = stats['memory_stats'].get('max_usage', memory_usage) / (1024 * 1024)
            
            # Парсим CPU
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
            
            # Получаем процесс в контейнере для детальной информации
            container_pid = self.container.attrs['State']['Pid']
            if container_pid:
                process = psutil.Process(container_pid)
                
                # Сетевые соединения
                connections = process.connections()
                tcp_connections = len([c for c in connections if c.type == psutil.SOCK_STREAM])
                
                # Открытые файлы
                open_files = len(process.open_files())
                
                # Потоки
                threads_count = process.num_threads()
                
                # Переключения контекста
                ctx_switches = process.num_ctx_switches().voluntary + process.num_ctx_switches().involuntary
            else:
                # Fallback значения
                connections = []
                tcp_connections = 0
                open_files = 0
                threads_count = 1
                ctx_switches = 0
            
            metrics = SystemMetrics(
                timestamp=time.time(),
                rss_mb=rss_mb,
                vms_mb=vms_mb,
                memory_percent=memory_percent,
                cpu_percent=max(0, cpu_percent),  # Не может быть отрицательным
                network_connections=len(connections),
                tcp_connections=tcp_connections,
                open_files=open_files,
                threads_count=threads_count,
                context_switches=ctx_switches
            )
            
            self.metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            print(f"⚠️  Ошибка получения метрик: {e}")
            # Возвращаем базовые метрики
            return SystemMetrics(
                timestamp=time.time(),
                rss_mb=0.0,
                vms_mb=0.0,
                memory_percent=0.0,
                cpu_percent=0.0,
                network_connections=0,
                tcp_connections=0,
                open_files=0,
                threads_count=1,
                context_switches=0
            )
    
    def detect_memory_leak_patterns(self) -> Dict:
        """
        Анализирует паттерны утечек памяти
        """
        if len(self.metrics_history) < 10:
            return {"status": "insufficient_data", "message": "Недостаточно данных для анализа"}
        
        # Анализируем последние 10 измерений
        recent_metrics = self.metrics_history[-10:]
        
        # Рост памяти
        memory_growth = recent_metrics[-1].rss_mb - recent_metrics[0].rss_mb
        
        # Рост сетевых соединений
        conn_growth = recent_metrics[-1].tcp_connections - recent_metrics[0].tcp_connections
        
        # Рост файловых дескрипторов
        files_growth = recent_metrics[-1].open_files - recent_metrics[0].open_files
        
        # Определяем типы утечек
        leak_types = []
        
        if memory_growth > 10:  # Рост памяти > 10 MB
            leak_types.append("memory_leak")
            
        if conn_growth > 5:  # Рост соединений > 5
            leak_types.append("connection_leak")
            
        if files_growth > 10:  # Рост файлов > 10
            leak_types.append("file_descriptor_leak")
        
        # Анализ тренда
        memory_values = [m.rss_mb for m in recent_metrics]
        trend = "increasing" if memory_values[-1] > memory_values[0] else "stable"
        
        return {
            "status": "analyzed",
            "leak_types": leak_types,
            "memory_growth_mb": memory_growth,
            "connection_growth": conn_growth,
            "files_growth": files_growth,
            "trend": trend,
            "severity": "high" if len(leak_types) >= 2 else "medium" if leak_types else "low"
        }
    
    def export_metrics_to_json(self, filename: str = None) -> str:
        """
        Экспортирует метрики в JSON для дальнейшего анализа
        """
        if not filename:
            filename = f"metrics_{self.container_name}_{int(time.time())}.json"
        
        data = {
            "container": self.container_name,
            "monitoring_period": {
                "start": self.metrics_history[0].timestamp if self.metrics_history else time.time(),
                "end": self.metrics_history[-1].timestamp if self.metrics_history else time.time(),
                "duration_minutes": len(self.metrics_history) * 5 / 60  # Предполагаем измерения каждые 5 сек
            },
            "leak_analysis": self.detect_memory_leak_patterns(),
            "metrics": [
                {
                    "timestamp": m.timestamp,
                    "datetime": datetime.fromtimestamp(m.timestamp).isoformat(),
                    "memory": {
                        "rss_mb": m.rss_mb,
                        "vms_mb": m.vms_mb,
                        "percent": m.memory_percent
                    },
                    "cpu_percent": m.cpu_percent,
                    "network": {
                        "total_connections": m.network_connections,
                        "tcp_connections": m.tcp_connections
                    },
                    "files": {
                        "open_files": m.open_files
                    },
                    "system": {
                        "threads": m.threads_count,
                        "context_switches": m.context_switches
                    }
                }
                for m in self.metrics_history
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Метрики экспортированы в {filename}")
        return filename
    
    def print_summary(self):
        """
        Выводит краткую сводку мониторинга
        """
        if not self.metrics_history:
            print("❌ Нет данных для анализа")
            return
        
        first = self.metrics_history[0]
        last = self.metrics_history[-1] 
        
        print(f"\n📊 СВОДКА МОНИТОРИНГА: {self.container_name}")
        print("=" * 60)
        print(f"⏱️  Период мониторинга: {len(self.metrics_history)} измерений")
        print(f"📈 Память RSS: {first.rss_mb:.1f} → {last.rss_mb:.1f} MB (Δ{last.rss_mb-first.rss_mb:+.1f})")
        print(f"💾 Память VMS: {first.vms_mb:.1f} → {last.vms_mb:.1f} MB (Δ{last.vms_mb-first.vms_mb:+.1f})")
        print(f"🔗 TCP соединения: {first.tcp_connections} → {last.tcp_connections} (Δ{last.tcp_connections-first.tcp_connections:+d})")
        print(f"📁 Открытые файлы: {first.open_files} → {last.open_files} (Δ{last.open_files-first.open_files:+d})")
        print(f"🧵 Потоки: {first.threads_count} → {last.threads_count} (Δ{last.threads_count-first.threads_count:+d})")
        
        # Анализ утечек
        leak_analysis = self.detect_memory_leak_patterns()
        print(f"\n🎯 АНАЛИЗ УТЕЧЕК:")
        print(f"   Серьезность: {leak_analysis.get('severity', 'unknown')}")
        print(f"   Типы утечек: {', '.join(leak_analysis.get('leak_types', []))}")
        print(f"   Тренд: {leak_analysis.get('trend', 'unknown')}")
        print("=" * 60)


# Пример использования в тестах
if __name__ == "__main__":
    # Демо без реального контейнера
    print("🧪 Демо EnhancedMemoryMonitor")
    
    # Создаем фейковые метрики для демонстрации
    class FakeContainer:
        name = "demo-container"
    
    monitor = EnhancedMemoryMonitor(FakeContainer())
    
    # Добавляем тестовые данные
    for i in range(20):
        metrics = SystemMetrics(
            timestamp=time.time() + i * 10,
            rss_mb=50 + i * 2,  # Рост памяти
            vms_mb=200 + i * 1.5,
            memory_percent=20 + i * 0.5,
            cpu_percent=15.0,
            network_connections=10 + i,  # Рост соединений
            tcp_connections=5 + i // 2,
            open_files=20 + i,  # Рост файлов
            threads_count=4,
            context_switches=1000 + i * 10
        )
        monitor.metrics_history.append(metrics)
    
    # Выводим сводку
    monitor.print_summary()
    
    # Экспортируем в JSON
    json_file = monitor.export_metrics_to_json("demo_metrics.json")
    print(f"✅ Создан файл: {json_file}")