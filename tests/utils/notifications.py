"""
Система уведомлений для Memory Leak CI
Поддерживает Slack, Teams, Email, Telegram
"""
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import os


@dataclass
class TestResult:
    """Результат теста на утечки памяти"""
    test_name: str
    status: str  # "passed", "failed", "error"
    duration_minutes: float
    memory_growth_mb: float
    leak_types: List[str]
    severity: str  # "low", "medium", "high", "critical"
    report_url: Optional[str] = None


class NotificationManager:
    """
    Менеджер уведомлений о результатах тестов
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
    def format_test_results(self, results: List[TestResult]) -> Dict:
        """Форматирует результаты тестов для уведомлений"""
        
        total_tests = len(results)
        passed = len([r for r in results if r.status == "passed"])
        failed = len([r for r in results if r.status == "failed"])
        errors = len([r for r in results if r.status == "error"])
        
        # Определяем общий статус
        if errors > 0:
            overall_status = "🔴 ERROR"
            status_emoji = "🔴"
        elif failed > 0:
            overall_status = "⚠️ FAILED"
            status_emoji = "⚠️"
        else:
            overall_status = "✅ PASSED"
            status_emoji = "✅"
        
        # Находим критичные утечки
        critical_leaks = [r for r in results if r.severity == "critical"]
        high_leaks = [r for r in results if r.severity == "high"]
        
        return {
            "overall_status": overall_status,
            "status_emoji": status_emoji,
            "stats": {
                "total": total_tests,
                "passed": passed,  
                "failed": failed,
                "errors": errors
            },
            "critical_leaks": len(critical_leaks),
            "high_leaks": len(high_leaks),
            "results": results
        }
    
    def send_slack_notification(self, results: List[TestResult], webhook_url: str):
        """Отправляет уведомление в Slack"""
        
        formatted = self.format_test_results(results)
        
        # Формируем детали по тестам
        test_details = []
        for result in results:
            emoji = "✅" if result.status == "passed" else "❌" if result.status == "failed" else "⚠️"
            leak_info = f" (Утечки: {', '.join(result.leak_types)})" if result.leak_types else ""
            test_details.append(
                f"{emoji} *{result.test_name}* - {result.duration_minutes:.1f}м, "
                f"память: {result.memory_growth_mb:+.1f}MB{leak_info}"
            )
        
        # Slack message payload
        payload = {
            "username": "Memory Leak CI Bot",
            "icon_emoji": ":mag:",
            "attachments": [
                {
                    "color": "good" if formatted["overall_status"].startswith("✅") else "danger",
                    "title": f"{formatted['status_emoji']} Memory Leak Detection CI Results",
                    "fields": [
                        {
                            "title": "Общий статус",
                            "value": formatted["overall_status"],
                            "short": True
                        },
                        {
                            "title": "Статистика",
                            "value": f"Всего: {formatted['stats']['total']}\n"
                                   f"✅ Прошли: {formatted['stats']['passed']}\n"
                                   f"❌ Упали: {formatted['stats']['failed']}\n"
                                   f"⚠️ Ошибки: {formatted['stats']['errors']}",
                            "short": True
                        },
                        {
                            "title": "Критичные утечки",
                            "value": f"🔴 Критичные: {formatted['critical_leaks']}\n"
                                   f"⚠️ Высокие: {formatted['high_leaks']}",
                            "short": True
                        },
                        {
                            "title": "Детали тестов",
                            "value": "\n".join(test_details[:5]) + ("\n..." if len(test_details) > 5 else ""),
                            "short": False
                        }
                    ],
                    "footer": "Memory Leak CI",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        # Добавляем ссылку на отчет если есть
        if any(r.report_url for r in results):
            report_url = next(r.report_url for r in results if r.report_url)
            payload["attachments"][0]["fields"].append({
                "title": "📊 Allure отчет",
                "value": f"<{report_url}|Открыть отчет>",
                "short": False
            })
        
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            print("✅ Slack уведомление отправлено")
        except Exception as e:
            print(f"❌ Ошибка отправки в Slack: {e}")
    
    def send_teams_notification(self, results: List[TestResult], webhook_url: str):
        """Отправляет уведомление в Microsoft Teams"""
        
        formatted = self.format_test_results(results)
        
        # Teams adaptive card
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "00FF00" if formatted["overall_status"].startswith("✅") else "FF0000",
            "summary": "Memory Leak CI Results",
            "sections": [
                {
                    "activityTitle": f"{formatted['status_emoji']} Memory Leak Detection CI",
                    "activitySubtitle": f"Результаты тестирования - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "facts": [
                        {"name": "Общий статус", "value": formatted["overall_status"]},
                        {"name": "Всего тестов", "value": str(formatted['stats']['total'])},
                        {"name": "Прошли", "value": str(formatted['stats']['passed'])},
                        {"name": "Упали", "value": str(formatted['stats']['failed'])},
                        {"name": "Критичные утечки", "value": str(formatted['critical_leaks'])},
                        {"name": "Высокие утечки", "value": str(formatted['high_leaks'])}
                    ],
                    "markdown": True
                }
            ]
        }
        
        # Добавляем детали тестов
        test_summary = []
        for result in results[:3]:  # Первые 3 теста
            emoji = "✅" if result.status == "passed" else "❌"
            test_summary.append(f"{emoji} {result.test_name}: {result.memory_growth_mb:+.1f}MB")
        
        if test_summary:
            card["sections"].append({
                "title": "Детали тестов",
                "text": "\n\n".join(test_summary)
            })
        
        # Добавляем кнопку отчета
        if any(r.report_url for r in results):
            report_url = next(r.report_url for r in results if r.report_url)
            card["potentialAction"] = [
                {
                    "@type": "OpenUri",
                    "name": "📊 Открыть Allure отчет",
                    "targets": [{"os": "default", "uri": report_url}]
                }
            ]
        
        try:
            response = requests.post(webhook_url, json=card, timeout=10)
            response.raise_for_status()
            print("✅ Teams уведомление отправлено")
        except Exception as e:
            print(f"❌ Ошибка отправки в Teams: {e}")
    
    def send_email_notification(self, results: List[TestResult], 
                              smtp_config: Dict, to_emails: List[str]):
        """Отправляет email уведомление"""
        
        formatted = self.format_test_results(results)
        
        # HTML email template
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>{formatted['status_emoji']} Memory Leak Detection CI Results</h2>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h3>📊 Общая статистика</h3>
                <ul>
                    <li><strong>Общий статус:</strong> {formatted['overall_status']}</li>
                    <li><strong>Всего тестов:</strong> {formatted['stats']['total']}</li>
                    <li><strong>✅ Прошли:</strong> {formatted['stats']['passed']}</li>
                    <li><strong>❌ Упали:</strong> {formatted['stats']['failed']}</li>
                    <li><strong>⚠️ Ошибки:</strong> {formatted['stats']['errors']}</li>
                    <li><strong>🔴 Критичные утечки:</strong> {formatted['critical_leaks']}</li>
                    <li><strong>⚠️ Высокие утечки:</strong> {formatted['high_leaks']}</li>
                </ul>
            </div>
            
            <h3>📋 Детали тестов</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px;">Тест</th>
                    <th style="padding: 8px;">Статус</th>
                    <th style="padding: 8px;">Время</th>
                    <th style="padding: 8px;">Рост памяти</th>
                    <th style="padding: 8px;">Утечки</th>
                    <th style="padding: 8px;">Серьезность</th>
                </tr>
        """
        
        for result in results:
            status_color = "green" if result.status == "passed" else "red"
            html_body += f"""
                <tr>
                    <td style="padding: 8px;">{result.test_name}</td>
                    <td style="padding: 8px; color: {status_color};">{result.status.upper()}</td>
                    <td style="padding: 8px;">{result.duration_minutes:.1f}м</td>
                    <td style="padding: 8px;">{result.memory_growth_mb:+.1f} MB</td>
                    <td style="padding: 8px;">{', '.join(result.leak_types) if result.leak_types else 'нет'}</td>
                    <td style="padding: 8px;">{result.severity}</td>
                </tr>
            """
        
        html_body += """
            </table>
            
            <p style="margin-top: 20px; color: #666;">
                Это автоматическое уведомление от Memory Leak Detection CI<br>
                Время: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
            </p>
        </body>
        </html>
        """
        
        # Создаем email
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{formatted['status_emoji']} Memory Leak CI: {formatted['overall_status']}"
        msg['From'] = smtp_config.get('from', 'memory-leak-ci@example.com')
        msg['To'] = ', '.join(to_emails)
        
        # Добавляем HTML версию
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        try:
            # Отправляем email
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                if smtp_config.get('use_tls'):
                    server.starttls()
                if smtp_config.get('username'):
                    server.login(smtp_config['username'], smtp_config['password'])
                
                server.send_message(msg)
            
            print(f"✅ Email уведомление отправлено на {len(to_emails)} адресов")
        except Exception as e:
            print(f"❌ Ошибка отправки email: {e}")
    
    def send_all_notifications(self, results: List[TestResult]):
        """Отправляет все настроенные уведомления"""
        
        # Slack
        if slack_webhook := os.getenv('SLACK_WEBHOOK_URL'):
            self.send_slack_notification(results, slack_webhook)
        
        # Teams  
        if teams_webhook := os.getenv('TEAMS_WEBHOOK_URL'):
            self.send_teams_notification(results, teams_webhook)
        
        # Email
        if all([os.getenv('SMTP_SERVER'), os.getenv('SMTP_FROM'), os.getenv('EMAIL_TO')]):
            smtp_config = {
                'server': os.getenv('SMTP_SERVER'),
                'port': int(os.getenv('SMTP_PORT', 587)),
                'username': os.getenv('SMTP_USERNAME'),
                'password': os.getenv('SMTP_PASSWORD'),
                'from': os.getenv('SMTP_FROM'),
                'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
            }
            to_emails = os.getenv('EMAIL_TO').split(',')
            self.send_email_notification(results, smtp_config, to_emails)


# Пример использования
if __name__ == "__main__":
    # Демо результаты тестов
    demo_results = [
        TestResult(
            test_name="test_app_with_leak_10min",
            status="failed",
            duration_minutes=10.2,
            memory_growth_mb=127.5,
            leak_types=["memory_leak", "connection_leak"],
            severity="critical",
            report_url="https://example.com/allure-report"
        ),
        TestResult(
            test_name="test_app_without_leak_10min", 
            status="passed",
            duration_minutes=10.1,
            memory_growth_mb=5.2,
            leak_types=[],
            severity="low"
        )
    ]
    
    # Демо уведомлений
    notifier = NotificationManager()
    
    print("📧 Демо форматирования результатов:")
    formatted = notifier.format_test_results(demo_results)
    print(json.dumps(formatted, indent=2, ensure_ascii=False))