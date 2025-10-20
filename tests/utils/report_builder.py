"""
Построение отчетов и графиков для Allure
"""
import matplotlib
matplotlib.use('Agg')  # Используем без GUI
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict
import os


class ReportBuilder:
    """
    Создание графиков и анализ данных для отчетов
    """
    
    def __init__(self, output_dir: str = "tests/allure-results"):
        """
        Args:
            output_dir: Директория для сохранения графиков
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Настройка стиля графиков
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def create_memory_chart(self, data: List[Dict], title: str, filename: str) -> str:
        """
        Создает график потребления памяти
        
        Args:
            data: Список измерений с ключами 'time', 'rss_mb', 'vms_mb'
            title: Заголовок графика
            filename: Имя файла для сохранения
        
        Returns:
            str: Путь к сохраненному файлу
        """
        if not data:
            return None
        
        # Извлекаем данные
        times = [d['time'] / 60 for d in data]  # Конвертируем в минуты
        rss = [d['rss_mb'] for d in data]
        vms = [d.get('vms_mb', d['rss_mb']) for d in data]
        
        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Основные линии
        ax.plot(times, rss, label='RSS (Resident Set Size)', 
                linewidth=2, color='#e74c3c', marker='o', markersize=3)
        ax.plot(times, vms, label='VMS (Virtual Memory Size)', 
                linewidth=2, color='#3498db', marker='s', markersize=3, alpha=0.7)
        
        # Линия тренда для RSS
        if len(times) > 2:
            z = np.polyfit(times, rss, 1)
            p = np.poly1d(z)
            ax.plot(times, p(times), "--", label=f'Тренд RSS (наклон: {z[0]:.2f} MB/мин)', 
                   linewidth=2, color='#c0392b', alpha=0.6)
        
        # Заполнение области под RSS
        ax.fill_between(times, 0, rss, alpha=0.2, color='#e74c3c')
        
        # Аннотации начала и конца
        ax.annotate(f'Начало: {rss[0]:.1f} MB', 
                   xy=(times[0], rss[0]), 
                   xytext=(times[0] + 0.5, rss[0] + 20),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2),
                   fontsize=10, color='green', weight='bold')
        
        ax.annotate(f'Конец: {rss[-1]:.1f} MB\nРост: +{rss[-1] - rss[0]:.1f} MB', 
                   xy=(times[-1], rss[-1]), 
                   xytext=(times[-1] - 2, rss[-1] + 20),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2),
                   fontsize=10, color='red', weight='bold')
        
        # Настройка осей и сетки
        ax.set_xlabel('Время (минуты)', fontsize=12, weight='bold')
        ax.set_ylabel('Память (MB)', fontsize=12, weight='bold')
        ax.set_title(title, fontsize=14, weight='bold', pad=20)
        ax.legend(loc='upper left', fontsize=11)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Добавляем информацию о росте
        growth = rss[-1] - rss[0]
        duration = times[-1]
        growth_rate = growth / duration if duration > 0 else 0
        
        info_text = f'📊 Статистика:\n'
        info_text += f'Рост памяти: {growth:.2f} MB\n'
        info_text += f'Скорость: {growth_rate:.2f} MB/мин\n'
        info_text += f'Длительность: {duration:.1f} мин'
        
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Сохранение
        filepath = os.path.join(self.output_dir, filename)
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 График сохранен: {filepath}")
        return filepath
    
    def create_comparison_chart(self, data_leak: List[Dict], data_no_leak: List[Dict], 
                                title: str, filename: str) -> str:
        """
        Создает сравнительный график для двух приложений
        """
        if not data_leak or not data_no_leak:
            return None
        
        # Извлекаем данные
        times_leak = [d['time'] / 60 for d in data_leak]
        rss_leak = [d['rss_mb'] for d in data_leak]
        
        times_no_leak = [d['time'] / 60 for d in data_no_leak]
        rss_no_leak = [d['rss_mb'] for d in data_no_leak]
        
        # Создаем фигуру с двумя подграфиками
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # График 1: Сравнение на одном графике
        ax1.plot(times_leak, rss_leak, label='С утечкой памяти', 
                linewidth=2.5, color='#e74c3c', marker='o', markersize=4)
        ax1.plot(times_no_leak, rss_no_leak, label='Без утечки памяти', 
                linewidth=2.5, color='#27ae60', marker='s', markersize=4)
        
        ax1.fill_between(times_leak, 0, rss_leak, alpha=0.2, color='#e74c3c')
        ax1.fill_between(times_no_leak, 0, rss_no_leak, alpha=0.2, color='#27ae60')
        
        ax1.set_xlabel('Время (минуты)', fontsize=12, weight='bold')
        ax1.set_ylabel('Память RSS (MB)', fontsize=12, weight='bold')
        ax1.set_title('Сравнение потребления памяти', fontsize=14, weight='bold')
        ax1.legend(loc='upper left', fontsize=11)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # График 2: Разница в потреблении памяти
        # Интерполируем данные для одинаковой длины
        min_len = min(len(rss_leak), len(rss_no_leak))
        diff = [rss_leak[i] - rss_no_leak[i] for i in range(min_len)]
        times_diff = times_leak[:min_len]
        
        ax2.plot(times_diff, diff, label='Разница (Leak - No Leak)', 
                linewidth=2.5, color='#9b59b6', marker='D', markersize=4)
        ax2.fill_between(times_diff, 0, diff, alpha=0.3, color='#9b59b6')
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        
        ax2.set_xlabel('Время (минуты)', fontsize=12, weight='bold')
        ax2.set_ylabel('Разница в памяти (MB)', fontsize=12, weight='bold')
        ax2.set_title('Разница в потреблении памяти', fontsize=14, weight='bold')
        ax2.legend(loc='upper left', fontsize=11)
        ax2.grid(True, alpha=0.3, linestyle='--')
        
        # Статистика
        growth_leak = rss_leak[-1] - rss_leak[0]
        growth_no_leak = rss_no_leak[-1] - rss_no_leak[0]
        
        info_text = f'📊 Сравнительная статистика:\n'
        info_text += f'С утечкой: +{growth_leak:.2f} MB\n'
        info_text += f'Без утечки: +{growth_no_leak:.2f} MB\n'
        info_text += f'Разница: {growth_leak - growth_no_leak:.2f} MB\n'
        info_text += f'Соотношение: {growth_leak / max(growth_no_leak, 1):.2f}x'
        
        ax2.text(0.02, 0.98, info_text, transform=ax2.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # Сохранение
        filepath = os.path.join(self.output_dir, filename)
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Сравнительный график сохранен: {filepath}")
        return filepath
    
    def analyze_trend(self, data: List[Dict]) -> Dict:
        """
        Анализирует тренд изменения памяти
        
        Returns:
            dict: {
                'trend': str,              # 'increasing', 'decreasing', 'stable'
                'growth_rate': float,      # MB/мин
                'growth_coefficient': float,  # Коэффициент линейной регрессии
                'r_squared': float         # Качество аппроксимации
            }
        """
        if len(data) < 3:
            return {
                'trend': 'insufficient_data',
                'growth_rate': 0.0,
                'growth_coefficient': 0.0,
                'r_squared': 0.0
            }
        
        # Извлекаем данные
        times = np.array([d['time'] / 60 for d in data])  # минуты
        memory = np.array([d['rss_mb'] for d in data])
        
        # Линейная регрессия
        coefficients = np.polyfit(times, memory, 1)
        slope = coefficients[0]  # Наклон (MB/мин)
        
        # R-squared
        p = np.poly1d(coefficients)
        y_pred = p(times)
        ss_res = np.sum((memory - y_pred) ** 2)
        ss_tot = np.sum((memory - np.mean(memory)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Определяем тренд
        if slope > 3.0:  # Рост более 3 MB/мин
            trend = 'increasing'
        elif slope < -3.0:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Общий рост памяти
        total_growth = memory[-1] - memory[0]
        duration = times[-1] - times[0]
        avg_growth_rate = total_growth / duration if duration > 0 else 0
        
        return {
            'trend': trend,
            'growth_rate': avg_growth_rate,
            'growth_coefficient': slope,
            'r_squared': r_squared,
            'total_growth_mb': total_growth
        }
