import os
import sqlite3
from typing import List, Dict, Tuple

from app.config import DB_FILE
from app.models.investment import Investment


class InvestmentStorageService:
    def __init__(self):
        self.db_path = DB_FILE
        self._ensure_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS investments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    broker TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    description TEXT,
                    initial_amount REAL NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investment_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL,
                    FOREIGN KEY (investment_id) REFERENCES investments(id) ON DELETE CASCADE
                )
                """
            )

    # Investments
    def load_investments(self) -> List[Dict]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT name, broker, start_date, description, initial_amount FROM investments ORDER BY id ASC"
            )
            rows = cur.fetchall()
            return [
                {
                    "name": r[0],
                    "broker": r[1],
                    "start_date": r[2],
                    "description": r[3] or "",
                    "initial_amount": float(r[4] or 0.0),
                }
                for r in rows
            ]

    def save_investment(self, inv: Investment) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO investments (name, broker, start_date, description, initial_amount) VALUES (?, ?, ?, ?, ?)",
                (inv.name, inv.broker, inv.start_date, inv.description, float(inv.initial_amount)),
            )
            conn.commit()

    def _get_investment_id_by_index(self, index: int) -> int | None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id FROM investments ORDER BY id ASC LIMIT 1 OFFSET ?",
                (index,),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def update_investment(self, index: int, inv: Investment) -> None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id FROM investments ORDER BY id ASC LIMIT 1 OFFSET ?",
                (index,),
            )
            row = cur.fetchone()
            if row:
                conn.execute(
                    "UPDATE investments SET name = ?, broker = ?, start_date = ?, description = ?, initial_amount = ? WHERE id = ?",
                    (inv.name, inv.broker, inv.start_date, inv.description, float(inv.initial_amount), row[0]),
                )
                conn.commit()

    def delete_investment(self, index: int) -> None:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id FROM investments ORDER BY id ASC LIMIT 1 OFFSET ?",
                (index,),
            )
            row = cur.fetchone()
            if row:
                conn.execute("DELETE FROM investments WHERE id = ?", (row[0],))
                conn.commit()

    # Contributions
    def load_contributions(self, investment_index: int) -> List[Dict]:
        inv_id = self._get_investment_id_by_index(investment_index)
        if inv_id is None:
            return []
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT date, description, amount FROM contributions WHERE investment_id = ? ORDER BY id ASC",
                (inv_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "date": r[0],
                    "description": r[1] or "",
                    "amount": float(r[2] or 0.0),
                }
                for r in rows
            ]

    def save_contribution(self, investment_index: int, date: str, description: str, amount: float) -> None:
        inv_id = self._get_investment_id_by_index(investment_index)
        if inv_id is None:
            return
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO contributions (investment_id, date, description, amount) VALUES (?, ?, ?, ?)",
                (inv_id, date, description, float(amount)),
            )
            conn.commit()

    def delete_contribution(self, investment_index: int, contribution_index: int) -> None:
        inv_id = self._get_investment_id_by_index(investment_index)
        if inv_id is None:
            return
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id FROM contributions WHERE investment_id = ? ORDER BY id ASC LIMIT 1 OFFSET ?",
                (inv_id, contribution_index),
            )
            row = cur.fetchone()
            if row:
                conn.execute("DELETE FROM contributions WHERE id = ?", (row[0],))
                conn.commit()

    def get_total_invested(self) -> float:
        with self._connect() as conn:
            cur1 = conn.execute("SELECT COALESCE(SUM(initial_amount), 0) FROM investments")
            total_initial = float(cur1.fetchone()[0] or 0.0)
            cur2 = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM contributions")
            total_contrib = float(cur2.fetchone()[0] or 0.0)
            return total_initial + total_contrib

    def get_investment_contrib_sum(self, investment_index: int) -> float:
        inv_id = self._get_investment_id_by_index(investment_index)
        if inv_id is None:
            return 0.0
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE investment_id = ?",
                (inv_id,),
            )
            total = cur.fetchone()[0]
            return float(total or 0.0)