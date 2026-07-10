from dataclasses import dataclass


@dataclass
class InstrumentInfo:
    """One entry from a BANA §33.2 instrument-list header.

    part_number is the primary §33.2.2 numbering digit (e.g. "1" for
    "Violin I"); sub_number is the further-division digit (e.g. "1" for
    "Violins I-1"). Both are None when the instrument isn't numbered.
    """
    name: str
    abbreviation: str
    part_number: str | None = None
    sub_number: str | None = None
