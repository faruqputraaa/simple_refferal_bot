import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)
        await self.create_table()

    async def create_table(self):
        await self.pool.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_id BIGINT UNIQUE,
            username TEXT,
            referrer_id BIGINT,
            score INT DEFAULT 0
        );
        """)

    async def add_user(self, user_id, username, referrer_id=None):
        # Cek apakah user sudah ada
        exists = await self.pool.fetchval("SELECT 1 FROM users WHERE user_id=$1", user_id)
        if not exists:
            # Tambahkan user baru
            await self.pool.execute("""
            INSERT INTO users (user_id, username, referrer_id)
            VALUES ($1, $2, $3)
            """, user_id, username, referrer_id)

            # Tambahkan poin ke referrer jika ada
            if referrer_id:
                await self.pool.execute("""
                UPDATE users SET score = score + 1 WHERE user_id = $1
                """, referrer_id)

    async def get_score(self, user_id):
        score = await self.pool.fetchval("SELECT score FROM users WHERE user_id=$1", user_id)
        return score or 0

    async def get_leaderboard(self):
        rows = await self.pool.fetch("SELECT username, score FROM users ORDER BY score DESC LIMIT 10")
        return [(r['username'], r['score']) for r in rows]
