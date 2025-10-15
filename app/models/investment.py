from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Investment:
    name: str
    broker: str
    start_date: str  # formato YYYY-MM-DD
    description: str
    initial_amount: float

    def to_dict(self) -> Dict:
        return asdict(self)