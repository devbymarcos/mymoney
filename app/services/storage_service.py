import json
import os
import sqlite3
from typing import List, Dict

from app.config import EXPENSES_FILE, DB_FILE
from app.models.expense import Expense


class StorageService:
    def __init__(self, filepath: str = EXPENSES_FILE):
        # filepath mantido apenas para migração de dados do JSON
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
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    amount REAL NOT NULL
                )
                """
            )

    def _migrate_from_json_if_needed(self) -> None:
        # Se a tabela estiver vazia e existir dados no JSON, importa-os
        try:
            with self._connect() as conn:
                cur = conn.execute("SELECT COUNT(*) FROM expenses")
                count = cur.fetchone()[0]
                if count == 0 and os.path.exists(self.filepath):
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        data = json.load(f) or []
                    if data:
                        conn.executemany(
                            "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
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
            # Em caso de erro de migração, segue sem interromper o app
            pass

    def load_expenses(self) -> List[Dict]:
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT date, category, description, amount FROM expenses ORDER BY id ASC"
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

    def save_expense(self, expense: Expense) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
                (expense.date, expense.category, expense.description, float(expense.amount)),
            )
            conn.commit()

    def get_total(self) -> float:
        with self._connect() as conn:
            cur = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
            total = cur.fetchone()[0]
            return float(total or 0.0)

    def delete_expense(self, index: int) -> None:
        # Apaga com base no índice de linha atual (ordenado por id ASC)
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id FROM expenses ORDER BY id ASC LIMIT 1 OFFSET ?",
                (index,),
            )
            row = cur.fetchone()
            if row:
                conn.execute("DELETE FROM expenses WHERE id = ?", (row[0],))
                conn.commit()

    def update_expense(self, index: int, expense: Expense) -> None:
        # Atualiza com base no índice visual (ordenado por id ASC)
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT id FROM expenses ORDER BY id ASC LIMIT 1 OFFSET ?",
                (index,),
            )
            row = cur.fetchone()
            if row:
                conn.execute(
                    "UPDATE expenses SET date = ?, category = ?, description = ?, amount = ? WHERE id = ?",
                    (expense.date, expense.category, expense.description, float(expense.amount), row[0]),
                )
                conn.commit()