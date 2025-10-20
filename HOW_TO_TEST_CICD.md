# 🧪 Как протестировать CI/CD Pipeline

## 📋 Краткий обзор

Этот файл покажет как **легко и быстро** протестировать автоматические CI/CD pipeline'ы с минимальными изменениями кода.

---

## 🦊 **Тестирование GitLab CI/CD**

### 🚀 **Способ 1: Изменение README (самый простой)**

```bash
# 1. Сделайте небольшое изменение в README
echo "" >> README.MD
echo "<!-- Test GitLab CI: $(date) -->" >> README.MD

# 2. Commit и push
git add README.MD
git commit -m "test: проверка GitLab CI/CD pipeline"
git push

# 3. Наблюдайте результат в GitLab:
# Перейдите в: CI/CD > Pipelines
# Увидите: running → успешный pipeline с тестами
```

### 🔧 **Способ 2: Добавление тестового файла**

```bash
# 1. Создайте тестовый файл
cat > TEST_CICD.md << 'EOF'
# Test CI/CD Pipeline

Этот файл создан для тестирования автоматического CI/CD pipeline.

Время создания: $(date)
Пользователь: $(whoami)
EOF

# 2. Commit и push
git add TEST_CICD.md
git commit -m "feat: добавлен тестовый файл для CI/CD"
git push
```

### 🐛 **Способ 3: Имитация ошибки (для проверки уведомлений)**

```bash
# 1. Временно сломайте тест (например, измените критерий утечки)
# В файле tests/test_quick_demo.py найдите строку:
# is_leak = memory_growth > 20 and trend_analysis['trend'] == 'increasing'
# Измените на:
# is_leak = True  # Всегда считаем что есть утечка

# 2. Commit и push
git add tests/test_quick_demo.py
git commit -m "test: имитация ошибки для проверки уведомлений"
git push

# 3. Верните обратно после тестирования!
git revert HEAD
git push
```

---

## 🐙 **Тестирование GitHub Actions**

### 🚀 **Способ 1: Простое изменение**

```bash
# 1. Добавьте строку в любой файл
echo "# GitHub Actions test: $(date)" >> .gitignore

# 2. Push запустит workflow
git add .gitignore
git commit -m "ci: test GitHub Actions workflow"
git push

# 3. Смотрите результат:
# GitHub → Actions tab → Memory Leak Detection CI
```

### 🎯 **Способ 2: Ручной запуск с параметрами**

```bash
# 1. В GitHub перейдите в Actions
# 2. Выберите "Memory Leak Detection CI"
# 3. Нажмите "Run workflow"
# 4. Выберите тип тестов:
#    - quick: быстрые тесты (5 мин)
#    - full: полные тесты (15 мин)  
#    - performance: нагрузочные тесты
# 5. Нажмите "Run workflow"
```

### 📊 **Способ 3: Pull Request**

```bash
# 1. Создайте новую ветку
git checkout -b test-ci-cd

# 2. Сделайте изменение
echo "Test PR CI/CD" > TEST_PR.txt
git add TEST_PR.txt
git commit -m "test: проверка CI через Pull Request"

# 3. Push в новую ветку
git push -u origin test-ci-cd

# 4. Создайте Pull Request в GitHub
# CI/CD запустится автоматически для PR
```

---

## 📊 **Что наблюдать в результатах**

### ✅ **Успешный pipeline:**

**GitLab:**
```
✅ prepare    - Python окружение готово
✅ build      - Docker образы собраны  
✅ test-quick - Быстрые тесты прошли
📊 report     - Allure отчет создан
```

**GitHub:**
```
✅ quick-tests      - Быстрые тесты (5 мин)
✅ allure-report    - Отчет сгенерирован
✅ security-scan    - Проверка безопасности
📧 notify          - Уведомления отправлены
```

### 🔴 **Pipeline с обнаруженной утечкой:**

```
✅ prepare         - OK
✅ build          - OK  
❌ test-quick     - FAILED (утечка обнаружена!)
📊 report         - Отчет с графиками утечки
📧 notifications  - Уведомления в Slack/Email
```

### 📈 **Где смотреть отчеты:**

- **GitLab Pages**: `https://yourusername.gitlab.io/memory-leak-ci-demo`
- **GitHub Pages**: `https://yourusername.github.io/memory-leak-ci-demo`
- **Allure в artifacts**: Скачайте из CI/CD job'а

---

## 🧪 **Продвинутое тестирование**

### 🌙 **Ночные тесты**

```bash
# GitLab: CI/CD > Schedules > New schedule
# Установите: 0 2 * * * (каждую ночь в 2:00)
# Variable: CI_PIPELINE_SOURCE = schedule

# GitHub: уже настроено в workflow
# Cron: '0 2 * * *' (каждую ночь в 2:00 UTC)
```

### 📧 **Тестирование уведомлений**

```bash
# 1. Настройте webhook'и в переменных окружения:
# GitLab: Settings > CI/CD > Variables:
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
EMAIL_TO=your-email@company.com

# GitHub: Settings > Secrets:
# Добавьте те же переменные

# 2. Сделайте push - уведомления придут автоматически
```

### 🚀 **Тестирование разных веток**

```bash
# Быстрые тесты запускаются для ВСЕХ веток
git checkout -b feature/new-monitoring
echo "New feature" > FEATURE.md
git add FEATURE.md
git commit -m "feat: new monitoring feature"
git push -u origin feature/new-monitoring

# Полные тесты - только для main
git checkout main
git merge feature/new-monitoring
git push  # Запустит полные тесты
```

---

## 🎯 **Практические сценарии**

### 📊 **Сценарий 1: Разработчик добавил новый код**

```bash
# 1. Разработчик коммитит изменения
git add .
git commit -m "feat: добавил новый endpoint"
git push

# 2. Автоматически запускаются быстрые тесты (5 мин)
# 3. Если найдена утечка → уведомление в Slack
# 4. Разработчик получает отчет с графиками
# 5. Исправляет код и коммитит снова
```

### 🌙 **Сценарий 2: Ночное тестирование**

```bash
# 1. Каждую ночь в 2:00 запускаются полные тесты (15 мин)
# 2. Тестируются обе версии приложения
# 3. Генерируется подробный отчет
# 4. Отчет публикуется на Pages
# 5. Команда получает email с результатами
```

### 🚨 **Сценарий 3: Обнаружена критичная утечка**

```bash
# 1. CI обнаруживает рост памяти > 100 MB
# 2. Автоматически определяется тип утечки (DB connections)
# 3. Отправляются уведомления:
#    - Slack: с графиками и деталями
#    - Email: HTML отчет с таблицами
#    - Teams: adaptive card с кнопкой "Открыть отчет"
# 4. Разработчики видят проблему в реальном времени
```

---

## 💡 **Советы по тестированию**

### ✅ **DO's:**

- Тестируйте с небольшими изменениями
- Проверяйте уведомления с реальными webhook'ами
- Используйте разные ветки для тестирования
- Настройте расписание для ночных тестов

### ❌ **DON'Ts:**

- Не коммитьте сломанные тесты в main
- Не оставляйте тестовые файлы в репозитории
- Не забывайте убирать debug изменения
- Не тестируйте на production webhook'ах

---

## 🎉 **Ожидаемые результаты**

После успешного тестирования вы увидите:

1. **📊 Автоматические отчеты** на GitHub/GitLab Pages
2. **📧 Уведомления** в настроенных каналах  
3. **📈 Графики памяти** в Allure отчетах
4. **🔄 Полную автоматизацию** процесса обнаружения утечек
5. **📱 Live мониторинг** через веб-дашборд

**Итог:** Ваша команда получит **enterprise-ready систему** для автоматического обнаружения утечек памяти! 🚀