from dataclasses import dataclass
from enum import Enum


class DynamicLevel(Enum):
    PPP = "ppp"
    PP = "pp"
    P = "p"
    MP = "mp"
    MF = "mf"
    F = "f"
    FF = "ff"
    FFF = "fff"
    SF = "sf"
    SFZ = "sfz"
    FP = "fp"
    CRESCENDO = "cresc"
    DECRESCENDO = "decresc"


@dataclass
class Dynamic:
    level: DynamicLevel
