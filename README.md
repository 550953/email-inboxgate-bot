# InboxGate Bot

Telegram-бот для проверки Google-аккаунтов (Gmail).

Пользователь отправляет логин:пароль (один или списком) через WebApp → заказ попадает в очередь → сервер проверяет → бот присылает ZIP с результатами.

## Локальный запуск

```bash
# 1. Клонировать
git clone https://github.com/YOUR_USERNAME/inboxgate-bot.git
cd inboxgate-bot

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Создать .env из примера и заполнить
cp .env.example .env
# Отредактировать .env

# 5. Запустить
python -m bot.main
```

## Переменные окружения

| Переменная                   | Обязательная | Описание                          |
|-----------------------------|--------------|-----------------------------------|
| `TELEGRAM_BOT_TOKEN`        | да           | Токен бота от @BotFather          |
| `SUPABASE_URL`              | да           | URL проекта Supabase              |
| `SUPABASE_SERVICE_ROLE_KEY` | да           | Service Role ключ (полный доступ) |
| `WEBAPP_URL`                | да           | Ссылка на WebApp                  |
| `ADMIN_TELEGRAM_IDS`        | нет          | ID админов через запятую          |

## Деплой на Render (Background Worker)

1. Создай **Background Worker** (не Web Service).
2. Подключи репозиторий.
3. Настройки:

| Параметр       | Значение                          |
|----------------|-----------------------------------|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python -m bot.main`              |

4. В **Environment** добавь переменные (через Infisical или вручную):
   - `TELEGRAM_BOT_TOKEN`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `WEBAPP_URL`

Бот работает в режиме **long polling** — порт не нужен.

## Команды бота

- `/new` — Новая проверка (открыть WebApp)
- `/status <номер>` — Статус заказа
- `/my` — Мои последние заказы
- `/queue` — Состояние очереди сервера
- `/cancel` — Отменить последний заказ
- `/help` — Формат списка и лимиты

## Структура

```
.
├── bot/
│   ├── main.py              # точка входа
│   ├── config.py
│   ├── handlers/
│   ├── keyboards/
│   ├── middlewares/
│   ├── services/
│   └── utils/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```
