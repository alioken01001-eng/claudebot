import aiosqlite
import json
import time
from typing import Optional

DB_PATH = "project_memory.db"

async def init_db():
    """Ma'lumotlar bazasini yaratish"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  TEXT NOT NULL,
                agent       TEXT NOT NULL,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                timestamp   REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id          TEXT PRIMARY KEY,
                user_id     INTEGER NOT NULL,
                chat_id     INTEGER NOT NULL,
                title       TEXT,
                status      TEXT DEFAULT 'active',
                context     TEXT DEFAULT '{}',
                created_at  REAL NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  TEXT NOT NULL,
                agent       TEXT NOT NULL,
                type        TEXT NOT NULL,
                filename    TEXT,
                content     TEXT NOT NULL,
                iteration   INTEGER DEFAULT 0,
                timestamp   REAL NOT NULL
            )
        """)
        await db.commit()


async def create_project(project_id: str, user_id: int, chat_id: int, title: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO projects VALUES (?,?,?,?,?,?,?)",
            (project_id, user_id, chat_id, title, "active", "{}", time.time())
        )
        await db.commit()


async def add_message(project_id: str, agent: str, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages VALUES (NULL,?,?,?,?,?)",
            (project_id, agent, role, content, time.time())
        )
        await db.commit()


async def get_project_history(project_id: str, limit: int = 50) -> list:
    """Loyiha tarixi - barcha agentlarning gaplari"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT agent, role, content FROM messages WHERE project_id=? ORDER BY timestamp DESC LIMIT ?",
            (project_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
    return list(reversed(rows))


async def save_artifact(project_id: str, agent: str, art_type: str,
                        content: str, filename: str = "", iteration: int = 0):
    """Agent tomonidan yaratilgan kod/fayl saqlash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO artifacts VALUES (NULL,?,?,?,?,?,?,?)",
            (project_id, agent, art_type, filename, content, iteration, time.time())
        )
        await db.commit()


async def get_artifacts(project_id: str, art_type: str = None) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        if art_type:
            async with db.execute(
                "SELECT agent,type,filename,content,iteration FROM artifacts WHERE project_id=? AND type=? ORDER BY timestamp DESC",
                (project_id, art_type)
            ) as c:
                return await c.fetchall()
        else:
            async with db.execute(
                "SELECT agent,type,filename,content,iteration FROM artifacts WHERE project_id=? ORDER BY timestamp DESC",
                (project_id,)
            ) as c:
                return await c.fetchall()


async def update_project_context(project_id: str, key: str, value):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT context FROM projects WHERE id=?", (project_id,)) as c:
            row = await c.fetchone()
        ctx = json.loads(row[0]) if row else {}
        ctx[key] = value
        await db.execute("UPDATE projects SET context=? WHERE id=?", (json.dumps(ctx), project_id))
        await db.commit()


async def get_project_context(project_id: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT context FROM projects WHERE id=?", (project_id,)) as c:
            row = await c.fetchone()
    return json.loads(row[0]) if row else {}
