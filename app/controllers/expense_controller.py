from typing import List, Dict

from app.models.expense import Expense
from app.services.storage_service import StorageService


class ExpenseController:
    def __init__(self):
        self.storage = StorageService()

    def add_expense(self, date: str, category: str, description: str, amount: float) -> None:
        expense = Expense(date=date, category=category, description=description, amount=amount)
        self.storage.save_expense(expense)

    def list_expenses(self) -> List[Dict]:
        return self.storage.load_expenses()

    def total_expenses(self) -> float:
        return self.storage.get_total()

    def delete_expenses(self, indices: list[int]) -> None:
        for i in sorted(indices, reverse=True):
            self.storage.delete_expense(i)

    def update_expense(self, index: int, date: str, category: str, description: str, amount: float) -> None:
        expense = Expense(date=date, category=category, description=description, amount=amount)
        self.storage.update_expense(index, expense)