# 🔧 Настройка GitHub Pages для Allure отчетов

## Включение GitHub Pages

1. **Перейдите в настройки репозитория:**
   - GitHub.com → Ваш репозиторий → Settings

2. **Найдите секцию "Pages":**
   - В левом меню: Settings → Pages

3. **Настройте источник:**
   - Source: Deploy from a branch
   - Branch: `gh-pages` 
   - Folder: `/ (root)`

4. **Сохраните настройки**

## 🌐 После настройки

Allure отчеты будут доступны по адресу:
```
https://sermkaym1.github.io/memory-leak-ci-demo/allure-report/
```

## 🔍 Альтернативный просмотр

Если GitHub Pages не настроен, отчеты доступны в артефактах CI:

1. Перейдите в раздел Actions
2. Выберите последний запуск workflow
3. Скачайте артефакт `demo-allure-report`
4. Распакуйте и откройте `index.html`

## ⚡ Проверка

После push в main:
1. Дождитесь завершения CI (1-2 минуты)
2. Перейдите по ссылке GitHub Pages
3. Увидите красивые Allure отчеты с графиками!

## 🛠️ Решение проблем

Если GitHub Pages не работает:
- Проверьте права репозитория в Settings → Actions → General
- Убедитесь что Workflow permissions установлены в "Read and write permissions"
- Проверьте что ветка `gh-pages` создалась после запуска CI