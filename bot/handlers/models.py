"""
SQL-схема базы данных магазина.
Таблицы: categories, users, products, cart, orders, order_items.
"""

CREATE_CATEGORIES = """
CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
"""

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY,
    username   TEXT,
    full_name  TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

CREATE_PRODUCTS = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    price_stars INTEGER NOT NULL DEFAULT 0,
    price_rub   INTEGER NOT NULL DEFAULT 0,
    photo_id    TEXT    DEFAULT '',
    hidden      INTEGER NOT NULL DEFAULT 0,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL
);
"""

CREATE_CART = """
CREATE TABLE IF NOT EXISTS cart (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    qty        INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, product_id)
);
"""

CREATE_ORDERS = """
CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    total_stars INTEGER NOT NULL DEFAULT 0,
    total_rub   INTEGER NOT NULL DEFAULT 0,
    status      TEXT    NOT NULL DEFAULT 'pending',
    pay_method  TEXT    NOT NULL DEFAULT 'stars',
    created_at  TEXT    DEFAULT (datetime('now'))
);
"""

CREATE_ORDER_ITEMS = """
CREATE TABLE IF NOT EXISTS order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    price_stars INTEGER NOT NULL DEFAULT 0,
    price_rub   INTEGER NOT NULL DEFAULT 0,
    qty         INTEGER NOT NULL DEFAULT 1
);
"""

ALL_TABLES = [
    CREATE_CATEGORIES,
    CREATE_USERS,
    CREATE_PRODUCTS,
    CREATE_CART,
    CREATE_ORDERS,
    CREATE_ORDER_ITEMS,
]
