import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import json

DB_PATH = os.getenv("DATABASE_PATH", "/opt/vpn_bot/vpn_bot.db")


class Database:
    def __init__(self):
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Пользователи + рефералка + баланс
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                language TEXT DEFAULT 'ru',
                referrer_id INTEGER,
                balance INTEGER DEFAULT 0
            )
        ''')

        # Подписки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username_trusttunnel TEXT UNIQUE,
                server_code TEXT,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                config_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Платежи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount INTEGER,
                status TEXT DEFAULT 'pending',
                payment_id TEXT UNIQUE,
                external_id TEXT,
                plan_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP
            )
        ''')

        # Реферальные начисления (история)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_user_id INTEGER,
                payment_id TEXT,
                reward_amount INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    # --- Пользователи ---

    def add_user(self, user_id: int, username: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        conn.commit()
        conn.close()

    def ensure_user(self, user_id: int, username: Optional[str] = None, referrer_id: Optional[int] = None):
        """
        Создаёт пользователя, если его нет. referrer_id фиксируется только при первом заходе.
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row is None:
            cursor.execute(
                "INSERT INTO users (user_id, username, referrer_id) VALUES (?, ?, ?)",
                (user_id, username, referrer_id)
            )
        else:
            # Обновим username, но не перезаписываем referrer_id
            if username is not None:
                cursor.execute(
                    "UPDATE users SET username = ? WHERE user_id = ?",
                    (username, user_id)
                )

        conn.commit()
        conn.close()

    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, created_at, language, referrer_id, balance FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "user_id": row[0],
                "username": row[1],
                "created_at": row[2],
                "language": row[3],
                "referrer_id": row[4],
                "balance": row[5],
            }
        return None

    def get_referrer(self, user_id: int) -> Optional[int]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0] is not None:
            return int(row[0])
        return None

    # --- Баланс и реферальные вознаграждения ---

    def add_referral_reward(self, referrer_id: int, referred_user_id: int, payment_id: str, reward_amount: int) -> None:
        """
        Начисляет referrer'у reward_amount (в рублях) на баланс и пишет запись в историю.
        """
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # увеличиваем баланс
        cursor.execute(
            "UPDATE users SET balance = COALESCE(balance, 0) + ? WHERE user_id = ?",
            (reward_amount, referrer_id)
        )

        # пишем историю
        cursor.execute(
            '''
            INSERT INTO referral_rewards (referrer_id, referred_user_id, payment_id, reward_amount)
            VALUES (?, ?, ?, ?)
            ''',
            (referrer_id, referred_user_id, payment_id, reward_amount)
        )

        conn.commit()
        conn.close()

    def get_balance(self, user_id: int) -> int:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0] is not None:
            return int(row[0])
        return 0

    # --- Подписки ---

    def add_subscription(self, user_id: int, username_trusttunnel: str,
                         server_code: str, days: int, config_data: Dict) -> datetime:
        expires_at = datetime.now() + timedelta(days=days)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO subscriptions 
            (user_id, username_trusttunnel, server_code, expires_at, config_data) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username_trusttunnel, server_code, expires_at, json.dumps(config_data)))
        conn.commit()
        conn.close()

        return expires_at

    def get_active_subscriptions(self, user_id: int) -> List[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM subscriptions 
            WHERE user_id = ? AND is_active = 1 AND expires_at > ?
            ORDER BY expires_at DESC
        ''', (user_id, datetime.now()))

        rows = cursor.fetchall()
        conn.close()

        subscriptions = []
        for row in rows:
            subscriptions.append({
                "id": row[0],
                "username": row[2],
                "server": row[3],
                "expires_at": datetime.fromisoformat(row[4]),
                "config": json.loads(row[7]) if row[7] else {}
            })
        return subscriptions

    # --- Платежи ---

    def add_payment(self, user_id: int, amount: int, payment_id: str, plan_code: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payments (user_id, amount, payment_id, plan_code) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, amount, payment_id, plan_code))
        conn.commit()
        conn.close()

    def confirm_payment(self, payment_id: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE payments SET status = 'completed', paid_at = ? 
            WHERE payment_id = ?
        ''', (datetime.now(), payment_id))
        conn.commit()
        conn.close()

    def get_payment(self, payment_id: str) -> Optional[Dict]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "user_id": row[1],
                "amount": row[2],
                "status": row[3],
                "plan_code": row[6]
            }
        return None


db = Database()
