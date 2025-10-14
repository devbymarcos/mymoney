import json
import os
import sqlite3
from typing import List, Dict

from app.config import REVENUES_FILE, DB_FILE
from app.models.revenue import Revenue


class RevenueStorageService:
    def __init__(self, filepath: str = REVENUES_FILE):
        # filepath mantido para migração
        self.filepath = filepath
        self.db_path = DB_FILE
        self._ensure_db()
        self._migrate_from_json_if_needed()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS revenues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL
                )
                """
            )

    def _migrate_from_json_if_needed(self) -> None:
        try:
            with self._connect() as conn:
                cur = conn.execute("SELECT COUNT(*) FROM revenues")
                count = cur.fetchone()[0]
                if count == 0 and os.path.exists(self.filepath):
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        data = json.load(f) or []
                    if data:
                        conn.executemany(
                            "INSERT INTO revenues (date, category, description, amount) VALUES (?, ?, ?, ?)",
                            [
                                (
                                    item.get("date", ""),
                                    item.get("category", ""),
                                    item.get("description", ""),
                                    float(item.get("amount", 0.0)),
                                )
                                for item in data
                            ],
                        )
                        conn.commit()
        except Exception:
            pass

    def load_revenues(self) -> List[Dict]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT date, category, description, amount FROM revenues ORDER BY id ASC"
            )
            rows = cur.fetchall()
            return [
                {
                    "date": r[0],
                    "category": r[1],
                    "description": r[2] or "",
                    "amount": float(r[3] or 0.0),
                }
                for r in rows
            ]

    def save_revenue(self, revenue: Revenue) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO revenues (date, category, description, amount) VALUES (?, ?, ?, ?)",
                (revenue.date, revenue.category, revenue.description, float(revenue.amount)),
            )
            conn.commit()

    def get_total(self) -> float:
        with self._connect() as conn:
            cur = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM revenues")
            total = cur.fetchone()[0]
            return float(total or 0.0)

    def delete_revenue(self, index: int) -> None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id FROM revenues ORDER BY id ASC LIMIT 1 OFFSET ?",
                (index,),
            )
            row = cur.fetchone()
            if row:
                conn.execute("DELETE FROM revenues WHERE id = ?", (row[0],))
                conn.commit()

    def update_revenue(self, index: int, revenue: Revenue) -> None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id FROM revenues ORDER BY id ASC LIMIT 1 OFFSET ?",
                (index,),
            )
            row = cur.fetchone()
            if row:
                conn.execute(
                    "UPDATE revenues SET date = ?, category = ?, description = ?, amount = ? WHERE id = ?",
                    (revenue.date, revenue.category, revenue.description, float(revenue.amount), row[0]),
                )
                conn.commit()