from dataclasses import dataclass, field

from .measure import Measure


@dataclass
class Staff:
    name: str
    measures: list[Measure] = field(default_factory=list)

    def add_measure(self, measure: Measure) -> None:
        self.measures.append(measure)
