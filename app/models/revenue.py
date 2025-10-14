from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Revenue:
    date: str  # formato YYYY-MM-DD
    category: str
    description: str
    amount: float

    def to_dict(self) -> Dict:
        return asdict(self)