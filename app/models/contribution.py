from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Contribution:
    investment_id: int  # referência ao investimento
    date: str  # formato YYYY-MM-DD
    description: str
    amount: float

    def to_dict(self) -> Dict:
        return asdict(self)