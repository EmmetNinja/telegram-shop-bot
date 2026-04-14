<div align="center">

# telegram-shop-bot

Бесплатный production-ready шаблон Telegram-магазина на Python + aiogram 3

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-blue)](https://docs.aiogram.dev)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

</div>

---

> ### 🔥 Нужна полная версия?
> **[telegram-shop-bot-pro](https://boosty.to/botbase/posts/69e7812d-f033-4359-a6c8-9617c439608c)** — CryptoBot · Webhook + FastAPI · Рассылка · Экспорт Excel · Throttling · Loguru
>
> **[Купить на Boosty →](https://boosty.to/botbase/posts/69e7812d-f033-4359-a6c8-9617c439608c)**

---

## Возможности

| Функция | Бесплатно | [Pro](https://boosty.to/botbase/posts/69e7812d-f033-4359-a6c8-9617c439608c) |
|---|:---:|:---:|
| Каталог с категориями и пагинацией | ✅ | ✅ |
| Корзина | ✅ | ✅ |
| Оплата Telegram Stars | ✅ | ✅ |
| Оплата ЮKassa | ✅ | ✅ |
| Оплата CryptoBot (крипта) | — | ✅ |
| Админка: добавление товаров и категорий | ✅ | ✅ |
| Уведомления о заказах | ✅ | ✅ |
| Рассылка пользователям | — | ✅ |
| Экспорт заказов в Excel | — | ✅ |
| Webhook режим + FastAPI | — | ✅ |
| Throttling (защита от спама) | — | ✅ |
| Loguru: логи с ротацией и zip | — | ✅ |
| PostgreSQL + SQLAlchemy 2.0 + Alembic | ✅ | ✅ |
| Redis (FSM) | ✅ | ✅ |
| Docker Compose | ✅ | ✅ |
| Чистая архитектура (handlers → services → repositories) | ✅ | ✅ |
| Тесты pytest | ✅ | ✅ |

## Стек

**aiogram 3.x** · **PostgreSQL** + **SQLAlchemy 2.0** + **Alembic** · **Redis** · **Docker Compose** · **pydantic-settings**

## Быстрый старт

### Docker (рекомендуется)

```bash
cp .env.example .env
# Заполните BOT_TOKEN и ADMIN_IDS
docker compose up --build
```

Контейнер `bot` сам выполнит `alembic upgrade head` и запустит бота.

### Локально

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Запустите PostgreSQL и Redis, заполните .env
alembic upgrade head
python main.py
```

Требования: **Python 3.10+**, PostgreSQL 14+, Redis 6+.

## Переменные окружения

Скопируйте `.env.example` → `.env`:

| Переменная | Обязательно | Описание |
|---|:---:|---|
| `BOT_TOKEN` | ✅ | Токен от @BotFather |
| `ADMIN_IDS` | ✅ | Telegram user ID через запятую |
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | | `redis://localhost:6379/0` |
| `YOOKASSA_SHOP_ID` | | ID магазина ЮKassa |
| `YOOKASSA_SECRET_KEY` | | Секрет ЮKassa |
| `CATALOG_PAGE_SIZE` | | Товаров на страницу (default: 5) |

## Структура проекта

```
telegram-shop-bot/
├── bot/
│   ├── handlers/       # только роутинг Telegram
│   ├── services/       # вся бизнес-логика
│   ├── repositories/   # только SQL
│   ├── models/         # SQLAlchemy ORM
│   ├── middlewares/    # DB, Auth, Settings
│   └── keyboards/
├── alembic/            # миграции
├── tests/              # pytest (SQLite in-memory)
├── config.py           # pydantic-settings
├── main.py             # точка входа
├── docker-compose.yml
└── Dockerfile
```

Хендлеры не содержат SQL. Репозитории не знают про aiogram. Сервисы — чистая бизнес-логика.

## Миграции

```bash
# Применить
alembic upgrade head

# Создать новую после изменения моделей
alembic revision --autogenerate -m "описание"
```

DSN берётся из `DATABASE_URL` — `sqlalchemy.url` в `alembic.ini` не используется.

## Тесты

```bash
pytest tests/ -q
```

SQLite in-memory — PostgreSQL не нужен для запуска тестов.

## Полная версия

**[telegram-shop-bot-pro](https://github.com/EmmetNinja/telegram-shop-bot-pro)** — расширенная версия с CryptoBot, Webhook, рассылкой, экспортом Excel и throttling.

**[Купить на Boosty →](https://)**

## Лицензия

MIT — делай что хочешь, attribution приветствуется.
