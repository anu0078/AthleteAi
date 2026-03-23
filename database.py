import sqlite3
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'athleteai.db')


class Database:
    def __init__(self):
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    name         TEXT NOT NULL,
                    age          INTEGER,
                    sport        TEXT,
                    fitness_level TEXT,
                    language     TEXT DEFAULT 'en',
                    city         TEXT,
                    weight       TEXT,
                    height       TEXT,
                    gender       TEXT DEFAULT 'male',
                    photo_path   TEXT,
                    created_at   TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS plans (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id        INTEGER,
                    workout_plan   TEXT,
                    nutrition_plan TEXT,
                    created_at     TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS progress (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id      INTEGER,
                    completed    INTEGER DEFAULT 0,
                    notes        TEXT,
                    weight       REAL,
                    energy_level INTEGER DEFAULT 5,
                    created_at   TEXT DEFAULT (datetime('now'))
                );
            """)

    # ── Users ──────────────────────────────────────────────────────────────────

    def create_user(self, name, age, sport, fitness_level, language='en',
                    city='', weight='', height='', gender='male', photo_path=None):
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO users (name, age, sport, fitness_level, language,
                   city, weight, height, gender, photo_path)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (name, age, sport, fitness_level, language,
                 city, weight, height, gender, photo_path)
            )
            return cur.lastrowid

    def get_user(self, user_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id=?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    # ── Plans ──────────────────────────────────────────────────────────────────

    def save_plan(self, user_id, workout_plan, nutrition_plan):
        """Always saves a new plan — never reuses old ones."""
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO plans (user_id, workout_plan, nutrition_plan)
                   VALUES (?,?,?)""",
                (user_id, workout_plan, nutrition_plan)
            )
            return cur.lastrowid

    def get_latest_plan(self, user_id):
        """Returns None always — forces dashboard to generate a fresh plan."""
        return None

    # ── Progress ───────────────────────────────────────────────────────────────

    def log_progress(self, user_id, completed=False, notes='',
                     weight=None, energy_level=5):
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO progress (user_id, completed, notes, weight, energy_level)
                   VALUES (?,?,?,?,?)""",
                (user_id, int(completed), notes, weight, energy_level)
            )
            return cur.lastrowid

    def get_progress(self, user_id):
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM progress WHERE user_id=? ORDER BY created_at DESC LIMIT 30",
                (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_streak(self, user_id):
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT date(created_at) as day, MAX(completed) as done
                   FROM progress WHERE user_id=?
                   GROUP BY date(created_at)
                   ORDER BY day DESC""",
                (user_id,)
            ).fetchall()
        streak = 0
        for row in rows:
            if row['done']:
                streak += 1
            else:
                break
        return streak
