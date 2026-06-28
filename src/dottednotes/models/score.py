from dataclasses import dataclass, field

from .staff import Staff


@dataclass
class Score:
    title: str = ""
    composer: str = ""
    staves: list[Staff] = field(default_factory=list)

    def add_staff(self, staff: Staff) -> None:
        self.staves.append(staff)
