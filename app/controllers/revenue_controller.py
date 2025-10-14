from typing import List, Dict

from app.models.revenue import Revenue
from app.services.revenue_storage_service import RevenueStorageService


class RevenueController:
    def __init__(self):
        self.storage = RevenueStorageService()

    def add_revenue(self, date: str, category: str, description: str, amount: float) -> None:
        revenue = Revenue(date=date, category=category, description=description, amount=amount)
        self.storage.save_revenue(revenue)

    def list_revenues(self) -> List[Dict]:
        return self.storage.load_revenues()

    def total_revenues(self) -> float:
        return self.storage.get_total()

    def delete_revenues(self, indices: list[int]) -> None:
        for i in sorted(indices, reverse=True):
            self.storage.delete_revenue(i)

    def update_revenue(self, index: int, date: str, category: str, description: str, amount: float) -> None:
        revenue = Revenue(date=date, category=category, description=description, amount=amount)
        self.storage.update_revenue(index, revenue)