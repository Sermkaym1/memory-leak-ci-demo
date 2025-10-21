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
        times = [d['time'] for d in data]  # Оставляем в секундах для лучшей читаемости
        rss = [d['rss_mb'] for d in data]
        vms = [d.get('vms_mb', d['rss_mb']) for d in data]
        
        # Создаем фигуру
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Основные линии
        ax.plot(times, rss, label='RSS (Resident Set Size)', 
                linewidth=3, color='#e74c3c', marker='o', markersize=6)
        ax.plot(times, vms, label='VMS (Virtual Memory Size)', 
                linewidth=2, color='#3498db', marker='s', markersize=4, alpha=0.7)
        
        # Линия тренда для RSS
        if len(times) > 2:
            z = np.polyfit(times, rss, 1)
            p = np.poly1d(z)
            trend_mb_per_sec = z[0]
            trend_mb_per_min = trend_mb_per_sec * 60
            ax.plot(times, p(times), "--", label=f'Тренд RSS ({trend_mb_per_min:+.2f} MB/мин)', 
                   linewidth=2, color='#c0392b', alpha=0.6)
        
        # Заполнение области под RSS
        ax.fill_between(times, min(rss) * 0.9, rss, alpha=0.15, color='#e74c3c')
        
        # 🎨 УЛУЧШЕННЫЕ аннотации с умным позиционированием
        rss_range = max(rss) - min(rss)
        time_range = max(times) - min(times)
        
        # Определяем рост памяти для выбора цветов
        growth = rss[-1] - rss[0]
        
        # Аннотация начала - всегда зеленая (старт)
        start_y_offset = rss_range * 0.4 if rss[0] < np.median(rss) else -rss_range * 0.2
        ax.annotate(f'Начало: {rss[0]:.1f} MB', 
                   xy=(times[0], rss[0]), 
                   xytext=(times[0] + time_range * 0.15, rss[0] + start_y_offset),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2),
                   fontsize=11, color='green', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7))
        
        # Аннотация конца - цвет зависит от роста
        if growth > 5.0:  # Значительный рост
            end_color = 'red'
            verdict = 'УТЕЧКА!'
            bg_color = 'mistyrose'
        elif growth > 2.0:  # Умеренный рост
            end_color = 'orange'
            verdict = 'Рост'
            bg_color = 'moccasin'
        else:  # Стабильно
            end_color = 'darkgreen'
            verdict = 'ЗДОРОВО!'
            bg_color = 'lightgreen'
        
        end_y_offset = rss_range * 0.4 if rss[-1] < np.median(rss) else -rss_range * 0.3
        ax.annotate(f'Конец: {rss[-1]:.1f} MB\nРост: +{growth:.1f} MB\n{verdict}', 
                   xy=(times[-1], rss[-1]), 
                   xytext=(times[-1] - time_range * 0.25, rss[-1] + end_y_offset),
                   arrowprops=dict(arrowstyle='->', color=end_color, lw=2),
                   fontsize=11, color=end_color, weight='bold',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor=bg_color, alpha=0.8))
        
        # Настройка осей и сетки
        ax.set_xlabel('Время (секунды)', fontsize=12, weight='bold')
        ax.set_ylabel('Память (MB)', fontsize=12, weight='bold')
        ax.set_title(title, fontsize=14, weight='bold', pad=20)
        ax.legend(loc='upper left', fontsize=11)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Улучшенные оси
        ax.set_xlim(min(times) - time_range * 0.05, max(times) + time_range * 0.05)
        ax.set_ylim(min(rss) - rss_range * 0.1, max(max(rss), max(vms)) + rss_range * 0.3)
        
        # 📊 УЛУЧШЕННАЯ информация с вердиктом
        growth = rss[-1] - rss[0]
        duration_sec = times[-1] - times[0]
        duration_min = duration_sec / 60
        growth_rate_per_min = (growth / duration_min) if duration_min > 0 else 0
        
        # Определяем вердикт по росту
        if growth > 8.0:
            verdict_emoji = "🚨"
            verdict_text = "КРИТИЧЕСКАЯ УТЕЧКА"
            info_bg_color = 'mistyrose'
        elif growth > 4.0:
            verdict_emoji = "🔴" 
            verdict_text = "УТЕЧКА ОБНАРУЖЕНА"
            info_bg_color = 'moccasin'
        elif growth > 1.0:
            verdict_emoji = "⚠️"
            verdict_text = "НЕБОЛЬШОЙ РОСТ"
            info_bg_color = 'lightyellow'
        else:
            verdict_emoji = "✅"
            verdict_text = "СТАБИЛЬНО"
            info_bg_color = 'lightgreen'
        
        info_text = f'📊 Анализ памяти:\n'
        info_text += f'{verdict_emoji} Вердикт: {verdict_text}\n'
        info_text += f'📈 Рост: {growth:+.2f} MB\n'
        info_text += f'⚡ Скорость: {growth_rate_per_min:+.1f} MB/мин\n'
        info_text += f'⏱️ Время: {duration_sec:.0f}с'
        
        # Позиционируем информационный блок справа вверху, чтобы не перекрывал надписи
        ax.text(0.98, 0.98, info_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round,pad=0.5', facecolor=info_bg_color, alpha=0.9))
        
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
        
        # 🔥 УЛУЧШЕННЫЕ КРИТЕРИИ для определения утечки:
        total_growth = memory[-1] - memory[0]
        duration = times[-1] - times[0]
        avg_growth_rate = total_growth / duration if duration > 0 else 0
        
        # Для демо: более строгие критерии
        # Нормальный рост Python приложения: 1-2 MB за 30 сек = 2-4 MB/мин
        # Утечка: более 10 MB/мин или более 5 MB за 30 сек
        if duration < 1.0:  # Менее минуты - используем абсолютные значения
            if total_growth > 5.0:  # Более 5 MB за короткое время
                trend = 'increasing'
            elif total_growth < -2.0:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:  # Более минуты - используем скорость
            if slope > 10.0 or avg_growth_rate > 8.0:  # Более 8-10 MB/мин = утечка
                trend = 'increasing'
            elif slope < -3.0:
                trend = 'decreasing'
            else:
                trend = 'stable'
        
        return {
            'trend': trend,
            'growth_rate': avg_growth_rate,
            'growth_coefficient': slope,
            'r_squared': r_squared,
            'total_growth_mb': total_growth
        }
