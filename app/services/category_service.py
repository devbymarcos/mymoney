import os
import sqlite3
from typing import List

from app.config import DB_FILE


class CategoryService:
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
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK (type IN ('expense','revenue')),
                    UNIQUE(name, type)
                )
                """
            )
            # Seed defaults if empty
            cur = conn.execute("SELECT COUNT(*) FROM categories")
            if (cur.fetchone()[0] or 0) == 0:
                defaults_expense = ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Outros"]
                defaults_revenue = ["Salário", "Freelance", "Vendas", "Investimentos", "Outros"]
                conn.executemany(
                    "INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'expense')",
                    [(n,) for n in defaults_expense],
                )
                conn.executemany(
                    "INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'revenue')",
                    [(n,) for n in defaults_revenue],
                )
                conn.commit()

            # Sync from existing data (ensures legacy categories are present)
            try:
                # Expenses
                cur = conn.execute("SELECT DISTINCT category FROM expenses")
                for (name,) in cur.fetchall():
                    if name:
                        conn.execute(
                            "INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'expense')",
                            (name,),
                        )
                # Revenues
                cur = conn.execute("SELECT DISTINCT category FROM revenues")
                for (name,) in cur.fetchall():
                    if name:
                        conn.execute(
                            "INSERT OR IGNORE INTO categories (name, type) VALUES (?, 'revenue')",
                            (name,),
                        )
                conn.commit()
            except Exception:
                pass

    def list_by_type(self, cat_type: str) -> List[str]:
        assert cat_type in ("expense", "revenue")
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT name FROM categories WHERE type = ? ORDER BY name COLLATE NOCASE ASC",
                (cat_type,),
            )
            return [r[0] for r in cur.fetchall()]

    def add_category(self, name: str, cat_type: str) -> bool:
        assert cat_type in ("expense", "revenue")
        name = (name or "").strip()
        if not name:
            return False
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO categories (name, type) VALUES (?, ?)",
                    (name, cat_type),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Duplicate
                return False

    def rename_category(self, old_name: str, new_name: str, cat_type: str) -> bool:
        assert cat_type in ("expense", "revenue")
        old_name = (old_name or "").strip()
        new_name = (new_name or "").strip()
        if not old_name or not new_name or old_name == new_name:
            return False
        with self._connect() as conn:
            # Se já existe a nova, vamos apenas migrar os lançamentos e remover a antiga
            cur = conn.execute(
                "SELECT COUNT(*) FROM categories WHERE name = ? AND type = ?",
                (new_name, cat_type),
            )
            exists_new = (cur.fetchone()[0] or 0) > 0

            if cat_type == 'expense':
                conn.execute("UPDATE expenses SET category = ? WHERE category = ?", (new_name, old_name))
            else:
                conn.execute("UPDATE revenues SET category = ? WHERE category = ?", (new_name, old_name))

            if exists_new:
                # Remover antiga se existir
                conn.execute("DELETE FROM categories WHERE name = ? AND type = ?", (old_name, cat_type))
            else:
                # Atualizar nome na tabela de categorias
                conn.execute(
                    "UPDATE categories SET name = ? WHERE name = ? AND type = ?",
                    (new_name, old_name, cat_type),
                )
            conn.commit()
            return True

    def delete_category(self, name: str, cat_type: str, reassign_to: str | None = None) -> bool:
        assert cat_type in ("expense", "revenue")
        name = (name or "").strip()
        if not name:
            return False
        with self._connect() as conn:
            # Se há reatribuição, garantir que a categoria alvo exista
            if reassign_to:
                reassign_to = reassign_to.strip()
                if not reassign_to:
                    return False
                conn.execute(
                    "INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)",
                    (reassign_to, cat_type),
                )
                if cat_type == 'expense':
                    conn.execute("UPDATE expenses SET category = ? WHERE category = ?", (reassign_to, name))
                else:
                    conn.execute("UPDATE revenues SET category = ? WHERE category = ?", (reassign_to, name))
                conn.execute("DELETE FROM categories WHERE name = ? AND type = ?", (name, cat_type))
                conn.commit()
                return True

            # Sem reatribuição: bloquear se houver lançamentos
            if cat_type == 'expense':
                cur = conn.execute("SELECT COUNT(*) FROM expenses WHERE category = ?", (name,))
            else:
                cur = conn.execute("SELECT COUNT(*) FROM revenues WHERE category = ?", (name,))
            used_count = cur.fetchone()[0] or 0
            if used_count > 0:
                return False
            conn.execute("DELETE FROM categories WHERE name = ? AND type = ?", (name, cat_type))
            conn.commit()
            return True