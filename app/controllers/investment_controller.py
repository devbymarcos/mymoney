from typing import List, Dict

from app.models.investment import Investment
from app.services.investment_storage_service import InvestmentStorageService


class InvestmentController:
    def __init__(self):
        self.storage = InvestmentStorageService()

    # Investments
    def add_investment(self, name: str, broker: str, start_date: str, description: str, initial_amount: float) -> None:
        inv = Investment(name=name, broker=broker, start_date=start_date, description=description, initial_amount=initial_amount)
        self.storage.save_investment(inv)

    def list_investments(self) -> List[Dict]:
        return self.storage.load_investments()

    def update_investment(self, index: int, name: str, broker: str, start_date: str, description: str, initial_amount: float) -> None:
        inv = Investment(name=name, broker=broker, start_date=start_date, description=description, initial_amount=initial_amount)
        self.storage.update_investment(index, inv)

    def delete_investments(self, indices: list[int]) -> None:
        for i in sorted(indices, reverse=True):
            self.storage.delete_investment(i)

    # Contributions
    def list_contributions(self, investment_index: int) -> List[Dict]:
        return self.storage.load_contributions(investment_index)

    def add_contribution(self, investment_index: int, date: str, description: str, amount: float) -> None:
        self.storage.save_contribution(investment_index, date, description, amount)

    def delete_contributions(self, investment_index: int, indices: list[int]) -> None:
        for i in sorted(indices, reverse=True):
            self.storage.delete_contribution(investment_index, i)

    # Totals
    def total_invested(self) -> float:
        return self.storage.get_total_invested()

    def contributions_sum(self, investment_index: int) -> float:
        return self.storage.get_investment_contrib_sum(investment_index)