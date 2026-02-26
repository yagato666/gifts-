import aiosqlite
from typing import Optional, Any

DB_PATH = "db.sqlite3"

async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            referrer_id INTEGER,
            verified INTEGER DEFAULT 0,
            referral_rewarded INTEGER DEFAULT 0,
            referrals_count INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS withdraws(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gift_key TEXT NOT NULL,
            gift_name TEXT NOT NULL,
            cost INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        )
        """)
        await db.commit()

async def fetchone(query: str, params: tuple = ()) -> Optional[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            return await cur.fetchone()

async def fetchall(query: str, params: tuple = ()) -> list[aiosqlite.Row]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cur:
            return await cur.fetchall()

async def execute(query: str, params: tuple = ()) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query, params)
        await db.commit()

async def execute_returning_id(query: str, params: tuple = ()) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(query, params)
        await db.commit()
        return cur.lastrowid

# --- Users ---
async def get_user(user_id: int) -> Optional[aiosqlite.Row]:
    return await fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))

async def upsert_user(user_id: int, username: str | None, referrer_id: int | None) -> None:
    # If user exists -> update username only
    existing = await get_user(user_id)
    if existing:
        await execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        return

    await execute(
        "INSERT INTO users(user_id, username, referrer_id) VALUES(?,?,?)",
        (user_id, username, referrer_id),
    )

async def set_verified(user_id: int, verified: bool) -> None:
    await execute("UPDATE users SET verified = ? WHERE user_id = ?", (1 if verified else 0, user_id))

async def add_balance(user_id: int, amount: int) -> None:
    await execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))

async def subtract_balance(user_id: int, amount: int) -> None:
    await execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))

async def mark_referral_rewarded(user_id: int) -> None:
    await execute("UPDATE users SET referral_rewarded = 1 WHERE user_id = ?", (user_id,))

async def inc_referrals_count(user_id: int, amount: int = 1) -> None:
    await execute("UPDATE users SET referrals_count = referrals_count + ? WHERE user_id = ?", (amount, user_id))

# --- Withdraws ---
async def create_withdraw(user_id: int, gift_key: str, gift_name: str, cost: int) -> int:
    return await execute_returning_id(
        "INSERT INTO withdraws(user_id, gift_key, gift_name, cost) VALUES(?,?,?,?)",
        (user_id, gift_key, gift_name, cost),
    )

async def get_withdraw(withdraw_id: int) -> Optional[aiosqlite.Row]:
    return await fetchone("SELECT * FROM withdraws WHERE id = ?", (withdraw_id,))

async def set_withdraw_status(withdraw_id: int, status: str) -> None:
    await execute("UPDATE withdraws SET status = ? WHERE id = ?", (status, withdraw_id))

async def get_user_withdraws(user_id: int, limit: int = 20) -> list[aiosqlite.Row]:
    return await fetchall(
        "SELECT * FROM withdraws WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
async def admin_stats():
    users = await fetchone("SELECT COUNT(*) as c FROM users")
    verified = await fetchone("SELECT COUNT(*) as c FROM users WHERE verified = 1")

    total_coins = await fetchone("SELECT SUM(cost) as s FROM withdraws WHERE status='approved'")
    total_withdraws = await fetchone("SELECT COUNT(*) as c FROM withdraws")

    pending = await fetchone("SELECT COUNT(*) as c FROM withdraws WHERE status='pending'")
    approved = await fetchone("SELECT COUNT(*) as c FROM withdraws WHERE status='approved'")
    declined = await fetchone("SELECT COUNT(*) as c FROM withdraws WHERE status='declined'")

    return {
        "users": users["c"],
        "verified": verified["c"],
        "coins": total_coins["s"] or 0,
        "withdraws": total_withdraws["c"],
        "pending": pending["c"],
        "approved": approved["c"],
        "declined": declined["c"],
    }
