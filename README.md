# 🤖 Telegram Shop Bot — aiogram 3.x

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-blue.svg)](https://aiogram.dev)
[![SQLite](https://img.shields.io/badge/SQLite-aiosqlite-green.svg)](https://sqlite.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Готовый шаблон Telegram магазина на Python. Каталог с категориями, корзина, оплата через **Telegram Stars**, экспорт заказов в Excel, inline-поиск. Разворачивается за 10 минут.

> 🛒 **Полная версия с исходным кодом:** [boosty.to/botbase](https://boosty.to/botbase/posts/49c557dd-467a-411e-b486-379940bd7944)

---

## ✨ Возможности

| Функция | Описание |
|---|---|
| 📦 Каталог с категориями | Иерархическое меню: категория → товары → карточка |
| 🛒 Корзина | Добавление, удаление, очистка |
| ⭐ Оплата Telegram Stars | Нативная оплата без регистрации в банках |
| 💳 ЮКасса | Заглушка, готова к подключению |
| 🔍 Inline-поиск | `@бот запрос` — поиск товаров в любом чате |
| 📊 Экспорт в Excel | Два листа: сводка заказов + состав |
| 🔔 Уведомления админам | При каждой оплате с кнопками «Выполнить» и «Детали» |
| 👁 Скрытие товаров | Скрыть/показать без удаления |
| ⚙️ Админ-панель | Полное управление прямо в Telegram |
| 🗄 SQLite | Без внешних серверов, база создаётся сама |

---

## 🏗 Архитектура

```
shop_bot/
├── main.py                   # Точка входа, long polling
├── config.py                 # Токен, ADMIN_IDS, настройки
├── .env.example              # Шаблон переменных окружения
├── requirements.txt
└── bot/
    ├── handlers/
    │   ├── user.py           # Каталог, корзина, оплата, inline-поиск
    │   └── admin.py          # FSM добавления товаров, категории, заказы
    ├── keyboards/
    │   ├── user_kb.py        # Inline-клавиатуры пользователя
    │   └── admin_kb.py       # Клавиатуры админки
    ├── database/
    │   ├── db.py             # Все запросы к БД (транзакции)
    │   └── models.py         # SQL-схема таблиц
    ├── middlewares/
    │   ├── auth.py           # Флаг is_admin в каждом апдейте
    │   └── db_middleware.py  # Инъекция Database в хендлеры
    └── utils/
        ├── payments.py       # Stars инвойс + заглушка ЮКасса
        └── export.py         # Генерация Excel через openpyxl
```

**Таблицы БД:** `users` · `categories` · `products` · `cart` · `orders` · `order_items`

---

## ⚡ Быстрый старт

### 1. Клонируй репозиторий

```bash
git clone https://github.com/твой-ник/shop-bot.git
cd shop-bot
```

### 2. Создай виртуальное окружение

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

### 3. Установи зависимости

```bash
pip install -r requirements.txt
```

### 4. Настрой .env

```bash
cp .env.example .env
```

Открой `.env` и заполни:

```env
BOT_TOKEN=токен_от_BotFather
ADMIN_IDS=твой_user_id
```

Свой `user_id` можно узнать у бота [@userinfobot](https://t.me/userinfobot).

### 5. Запусти

```bash
python main.py
```

В логах появится сообщение о запуске. Открой бота в Telegram и отправь `/start`.

---

## 🔧 Переменные окружения

| Переменная | Описание | Пример |
|---|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather | `123456:ABC...` |
| `ADMIN_IDS` | ID администраторов через запятую | `123456,789012` |
| `DEFAULT_PRICE_DISPLAY` | Валюта по умолчанию: `stars` или `rub` | `stars` |
| `MIN_ORDER_STARS` | Минимальный заказ в Stars (0 = без лимита) | `0` |
| `YOOKASSA_SHOP_ID` | ID магазина ЮКасса (опционально) | `12345` |
| `YOOKASSA_SECRET_KEY` | Секретный ключ ЮКасса (опционально) | `test_...` |

---

## 💳 Оплата

### Telegram Stars
Работает сразу после включения платежей в [@BotFather](https://t.me/BotFather):
`Bot Settings → Payments → Stars`

### ЮКасса
В `bot/utils/payments.py` оставлена заглушка с подробными инструкциями по подключению. После регистрации на [yookassa.ru](https://yookassa.ru) добавь `YOOKASSA_SHOP_ID` и `YOOKASSA_SECRET_KEY` в `.env`.

---

## 🛠 Команды бота

| Команда | Доступ | Описание |
|---|---|---|
| `/start` | Все | Главное меню |
| `/admin` | Админы | Панель управления |
| `/cancel` | Все | Отмена текущего действия |
| `@бот запрос` | Все | Inline-поиск товаров |

---

## 📋 Требования

- Python **3.10+**
- Аккаунт Telegram
- Бот от [@BotFather](https://t.me/BotFather)

```
aiogram>=3.4.0,<4
aiosqlite>=0.19.0
python-dotenv>=1.0.0
openpyxl>=3.1.0
```

---

## 🚀 Деплой

### Railway (бесплатно для старта)
1. Загрузи код на GitHub
2. Зайди на [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Добавь переменные окружения в настройках
4. Готово — бот работает 24/7

### VPS
```bash
pip install -r requirements.txt
screen -S bot
python main.py
```

---

## 📦 Полная версия

Это демо-репозиторий. Полная версия с исходным кодом доступна на Boosty:

**👉 [boosty.to/botbase — 4 900 ₽](https://boosty.to/botbase/posts/49c557dd-467a-411e-b486-379940bd7944)**

Что входит:
- Весь исходный код без ограничений
- README с инструкцией по запуску
- `.env.example` с описанием всех переменных

---

## 📄 Лицензия

MIT — используй свободно в личных и коммерческих проектах.
