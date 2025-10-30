# 🔧 Autologist - Техническая документация

## 📁 Структура проекта

```
Autologist/
├── api_server.py              # Основной API сервер (Flask)
├── telegram_parser_v2.py      # Telegram парсер с улучшениями
├── frontend/
│   ├── dashboard_clean.html   # Основной веб-интерфейс (чистая версия)
│   ├── dashboard.html         # Исходный интерфейс (может содержать дубликаты)
│   └── test.html             # Тестовый интерфейс для отладки
├── config/
│   └── monitored_chats.json  # Конфигурация отслеживаемых чатов
├── data/
│   └── messages/             # Папка с сохраненными сообщениями
└── README_USAGE.md           # Инструкция для пользователя
```

## 🌐 API Endpoints

### Статус и управление
- `GET /api/status` - Статус системы
- `POST /api/parser/start` - Запуск парсера
- `POST /api/parser/stop` - Остановка парсера

### Управление чатами
- `GET /api/chats/all` - Все доступные чаты
- `GET /api/chats/monitored` - Отслеживаемые чаты
- `POST /api/chats/add` - Добавить чат в отслеживание
- `POST /api/chats/remove` - Удалить чат из отслеживания
- `DELETE /api/chats/<chat_id>/remove` - Удалить чат (альтернативный метод)

### Сообщения
- `GET /api/messages` - Все сообщения с пагинацией
- `GET /api/messages/recent` - Последние 20 сообщений
- `GET /api/search` - Поиск сообщений

### Статические файлы
- `GET /frontend/<filename>` - Веб-интерфейс
- `GET /config/<filename>` - Файлы конфигурации

## 🔨 Основные компоненты

### 1. API Server (api_server.py)
**Назначение:** REST API сервер на Flask для веб-интерфейса

**Основные классы:**
- `AutologistAPI` - Основной класс с бизнес-логикой

**Ключевые методы:**
- `load_chats_config()` - Загрузка конфигурации чатов
- `save_chats_config()` - Сохранение конфигурации
- `get_all_user_chats()` - Получение всех доступных чатов
- `add_chat_to_monitoring()` - Добавление чата в отслеживание
- `remove_chat_from_monitoring()` - Удаление чата

### 2. Telegram Parser (telegram_parser_v2.py)
**Назначение:** Мониторинг Telegram чатов и сохранение сообщений

**Основные функции:**
- Подключение к Telegram API
- Мониторинг указанных чатов
- Фильтрация по ключевым словам
- Сохранение сообщений в JSON формате

### 3. Web Interface (dashboard_clean.html)
**Назначение:** Современный веб-интерфейс для управления системой

**Технологии:**
- HTML5 + CSS3 (Material Design стиль)
- Vanilla JavaScript (ES6+)
- Firebase SDK (опционально)
- Fetch API для связи с сервером

**Основные функции JavaScript:**
- `showTab()` - Переключение между вкладками
- `loadStatus()` - Загрузка статуса системы
- `loadChats()` - Загрузка списка чатов
- `loadMessages()` - Загрузка сообщений
- `addChat()` - Добавление чата в отслеживание
- `removeChat()` - Удаление чата

## 🗂️ Формат данных

### Конфигурация чатов (monitored_chats.json)
```json
[
  {
    "chat_id": "-1001234567890",
    "title": "Название чата",
    "username": "@chatusername", 
    "keywords": ["груз", "доставка", "транспорт"],
    "active": true
  }
]
```

### Формат сообщения
```json
{
  "id": 12345,
  "chat_id": "-1001234567890",
  "chat_title": "Название чата",
  "sender_id": 987654321,
  "sender_username": "@username",
  "message": "Текст сообщения",
  "date": "2025-10-30T09:00:00",
  "timestamp": "1730280000"
}
```

## 🎨 UI/UX дизайн

### Цветовая схема (Material Design)
- **Основной:** #1a73e8 (Google Blue)
- **Успех:** #34a853 (Green)
- **Предупреждение:** #fbbc04 (Yellow)
- **Ошибка:** #ea4335 (Red)
- **Фон:** #f8f9fa (Light Gray)
- **Карточки:** #ffffff с тенью

### Компоненты интерфейса
- **Навигация:** Горизонтальная панель с вкладками
- **Карточки:** Закругленные углы, тени Material Design
- **Кнопки:** Плоские с эффектами hover
- **Формы:** Современные input поля с labels
- **Таблицы:** Адаптивные с четкими разделителями

## 🔐 Безопасность

### Текущие меры
- CORS настроен для локального доступа
- Валидация входных данных на сервере
- Обработка ошибок и исключений

### Рекомендации для продакшена
- Добавить аутентификацию
- Использовать HTTPS
- Валидировать все пользовательские данные
- Логирование действий пользователей

## 🚀 Развертывание

### Требования
- Python 3.8+
- Flask, Flask-CORS
- Telethon (для Telegram API)
- Современный браузер с поддержкой ES6

### Локальная установка
1. Установить зависимости: `pip install flask flask-cors telethon`
2. Настроить Telegram API ключи
3. Запустить: `python api_server.py`
4. Открыть: http://localhost:8080/frontend/dashboard_clean.html

### Продакшен
- Использовать Gunicorn/uWSGI вместо встроенного сервера Flask
- Настроить reverse proxy (nginx)
- Добавить SSL сертификаты
- Настроить логирование и мониторинг

## 🔧 Отладка

### Логи сервера
Сервер выводит логи в консоль:
```
🚛 Autologist API Server
🌐 Интерфейс: http://localhost:8080
📡 API: http://localhost:8080/api/
```

### Отладка JavaScript
Открыть Developer Tools (F12) → Console для просмотра ошибок

### Проверка API
Использовать curl или Postman:
```bash
curl http://localhost:8080/api/status
curl http://localhost:8080/api/chats/monitored
```

## 📊 Мониторинг

### Метрики системы
- Статус парсера (running/stopped)
- Количество отслеживаемых чатов
- Количество полученных сообщений
- Количество ошибок

### Файлы логов
- Сообщения сохраняются в `data/messages/`
- Конфигурация в `config/monitored_chats.json`

---
*Техническая документация версии 2.0* 🔧