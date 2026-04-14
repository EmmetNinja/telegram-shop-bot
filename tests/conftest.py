"""
Pytest: подставляет минимальные переменные до импорта приложения.

Тесты используют только SQLite (aiosqlite) in-memory в фикстурах — отдельный PostgreSQL
не нужен, CI может гонять pytest без БД.

Ограничение: SQLite не повторяет весь диалект PostgreSQL (например, часть raw SQL
или edge-кейсы asyncpg). Для регрессий под нагрузкой имеет смысл добавить отдельный
job с тестовым PostgreSQL.
"""
import os

os.environ.setdefault("BOT_TOKEN", "0:dummy")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from config import reset_settings_cache

reset_settings_cache()
