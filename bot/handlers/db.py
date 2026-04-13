"""
Асинхронная работа с SQLite через aiosqlite.
Все запросы к БД — здесь.
"""
from __future__ import annotations

import aiosqlite

from bot.database.models import ALL_TABLES

DB_PATH = "shop.db"


class Database:
    def __init__(self, path: str = DB_PATH) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")

    async def init(self) -> None:
        for sql in ALL_TABLES:
            await self._conn.execute(sql)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    async def upsert_user(self, user_id: int, username: str | None, full_name: str) -> None:
        await self._conn.execute(
            "INSERT INTO users (id, username, full_name) VALUES (?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name",
            (user_id, username, full_name),
        )
        await self._conn.commit()

    async def add_category(self, name: str) -> int:
        cur = await self._conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
        await self._conn.commit()
        return cur.lastrowid

    async def get_categories(self) -> list[aiosqlite.Row]:
        cur = await self._conn.execute("SELECT * FROM categories ORDER BY name")
        return await cur.fetchall()

    async def get_products_by_category(self, category_id: int) -> list[aiosqlite.Row]:
        cur = await self._conn.execute(
            "SELECT * FROM products WHERE category_id=? AND hidden=0 ORDER BY id", (category_id,)
        )
        return await cur.fetchall()

    async def get_products_uncategorized(self) -> list[aiosqlite.Row]:
        cur = await self._conn.execute(
            "SELECT * FROM products WHERE category_id IS NULL AND hidden=0 ORDER BY id"
        )
        return await cur.fetchall()

    async def get_products(self, include_hidden: bool = False) -> list[aiosqlite.Row]:
        if include_hidden:
            cur = await self._conn.execute("SELECT * FROM products ORDER BY id")
        else:
            cur = await self._conn.execute("SELECT * FROM products WHERE hidden=0 ORDER BY id")
        return await cur.fetchall()

    async def get_product(self, product_id: int) -> aiosqlite.Row | None:
        cur = await self._conn.execute("SELECT * FROM products WHERE id=?", (product_id,))
        return await cur.fetchone()

    async def toggle_product_visibility(self, product_id: int) -> bool:
        cur = await self._conn.execute("SELECT hidden FROM products WHERE id=?", (product_id,))
        row = await cur.fetchone()
        if not row:
            return False
        new_val = 0 if row["hidden"] else 1
        await self._conn.execute("UPDATE products SET hidden=? WHERE id=?", (new_val, product_id))
        await self._conn.commit()
        return bool(new_val)

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        await self._conn.execute(
            "INSERT INTO cart (user_id, product_id, qty) VALUES (?,?,1) "
            "ON CONFLICT(user_id, product_id) DO UPDATE SET qty = qty + 1",
            (user_id, product_id),
        )
        await self._conn.commit()

    async def get_cart(self, user_id: int) -> list[aiosqlite.Row]:
        cur = await self._conn.execute(
            "SELECT c.product_id, c.qty, p.name, p.price_stars, p.price_rub "
            "FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?",
            (user_id,),
        )
        return await cur.fetchall()

    async def remove_from_cart(self, user_id: int, product_id: int) -> None:
        await self._conn.execute("DELETE FROM cart WHERE user_id=? AND product_id=?", (user_id, product_id))
        await self._conn.commit()

    async def clear_cart(self, user_id: int) -> None:
        await self._conn.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
        await self._conn.commit()

    async def create_order(self, user_id: int, items: list[aiosqlite.Row], pay_method: str) -> int:
        total_stars = sum(r["price_stars"] * r["qty"] for r in items)
        total_rub = sum(r["price_rub"] * r["qty"] for r in items)
        try:
            await self._conn.execute("BEGIN")
            cur = await self._conn.execute(
                "INSERT INTO orders (user_id, total_stars, total_rub, pay_method) VALUES (?,?,?,?)",
                (user_id, total_stars, total_rub, pay_method),
            )
            order_id = cur.lastrowid
            for r in items:
                await self._conn.execute(
                    "INSERT INTO order_items (order_id, product_id, name, price_stars, price_rub, qty) VALUES (?,?,?,?,?,?)",
                    (order_id, r["product_id"], r["name"], r["price_stars"], r["price_rub"], r["qty"]),
                )
            await self._conn.execute("COMMIT")
        except Exception:
            await self._conn.execute("ROLLBACK")
            raise
        return order_id

    async def get_order_items(self, order_id: int) -> list[aiosqlite.Row]:
        cur = await self._conn.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,))
        return await cur.fetchall()

    async def get_order(self, order_id: int) -> aiosqlite.Row | None:
        cur = await self._conn.execute(
            "SELECT o.*, u.full_name, u.username FROM orders o "
            "LEFT JOIN users u ON o.user_id = u.id WHERE o.id=?",
            (order_id,),
        )
        return await cur.fetchone()

    async def set_order_paid(self, order_id: int) -> None:
        await self._conn.execute("UPDATE orders SET status='paid' WHERE id=?", (order_id,))
        await self._conn.commit()

    async def get_recent_orders(self, limit: int = 20) -> list[aiosqlite.Row]:
        cur = await self._conn.execute(
            "SELECT o.id, o.user_id, u.full_name, o.total_stars, o.total_rub, "
            "o.status, o.pay_method, o.created_at "
            "FROM orders o LEFT JOIN users u ON o.user_id = u.id "
            "ORDER BY o.id DESC LIMIT ?",
            (limit,),
        )
        return await cur.fetchall()

    async def get_all_orders_with_items(self) -> tuple[list, dict]:
        cur = await self._conn.execute(
            "SELECT o.id, o.user_id, u.full_name, o.total_stars, o.total_rub, "
            "o.status, o.pay_method, o.created_at "
            "FROM orders o LEFT JOIN users u ON o.user_id = u.id ORDER BY o.id DESC"
        )
        orders = await cur.fetchall()
        items_by_order: dict = {}
        for o in orders:
            cur2 = await self._conn.execute("SELECT * FROM order_items WHERE order_id=?", (o["id"],))
            items_by_order[o["id"]] = await cur2.fetchall()
        return list(orders), items_by_order

    async def get_admin_ids(self) -> list[int]:
        import config
        return config.ADMIN_IDS
