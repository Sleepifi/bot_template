from pathlib import Path
import aiosqlite

from app.config import ClientConfig

SCHEME="""
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id TEXT NOT NULL,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    is_available INTEGER NOT NULL DEFAULT 1
);
"""

class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self, cfg:ClientConfig):
        Path(self.path).parent.mkdir(exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(SCHEME)
            cur = await db.execute("SELECT COUNT(*) FROM categories")
            (count,) = await cur.fetchone()
            print(count)
            if count == 0:
                for pos,c in enumerate(cfg.categories):
                    await db.execute(
                        "INSERT INTO categories (id,title,position) VALUES(?,?,?)",
                        (c.id,c.title,pos)
                    )
                    for p in c.products:
                        await db.execute(
                            "INSERT INTO products (category_id, name, price, description) "
                            "VALUES (?, ?, ?, ?)",
                            (c.id, p.name, p.price, p.description),
                        )
            await db.commit()

    async def _fetch(self, query: str,params: tuple = (), one:bool = False):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(query,params)
            return await cur.fetchone() if one else await cur.fetchall()
    
    async def get_categories(self):
        return await self._fetch("SELECT id, title FROM categories ORDER BY position")

    async def get_category(self, category_id: str):
        return await self._fetch(
            "SELECT id, title FROM categories WHERE id = ?", (category_id,), one=True
        )
    
    async def get_products(self, category_id: str):
        return await self._fetch(
            "SELECT id, name, price FROM products "
            "WHERE category_id = ? AND is_available = 1 ORDER BY id",
            (category_id,),
        )

    async def get_product(self, product_id: int):
        return await self._fetch(
            "SELECT * FROM products WHERE id = ?", (product_id,), one=True
        )
    
    async def add_product(self, category_id: str, name: str, price: int, description: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO products (category_id, name, price, description) "
                "VALUES (?, ?, ?, ?)",
                (category_id, name, price, description),
            )
            await db.commit()