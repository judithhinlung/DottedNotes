from dataclasses import dataclass
from enum import Enum, auto


class DynamicLevel(Enum):
    PPP = auto()
    PP = auto()
    P = auto()
    MP = auto()
    MF = auto()
    F = auto()
    FF = auto()
    FFF = auto()
    SF = auto()
    SFZ = auto()
    FP = auto()
    CRESCENDO_START = auto()
    CRESCENDO_END = auto()
    DECRESCENDO_START = auto()
    DECRESCENDO_END = auto()


DYNAMIC_TO_LILYPOND = {
    DynamicLevel.PPP: r'\ppp',
    DynamicLevel.PP: r'\pp',
    DynamicLevel.P: r'\p',
    DynamicLevel.MP: r'\mp',
    DynamicLevel.MF: r'\mf',
    DynamicLevel.F: r'\f',
    DynamicLevel.FF: r'\ff',
    DynamicLevel.FFF: r'\fff',
    DynamicLevel.SF: r'\sf',
    DynamicLevel.SFZ: r'\sfz',
    DynamicLevel.FP: r'\fp',
    DynamicLevel.CRESCENDO_START: r'\<',
    DynamicLevel.CRESCENDO_END: r'\!',
    DynamicLevel.DECRESCENDO_START: r'\>',
    DynamicLevel.DECRESCENDO_END: r'\!',
}


_DYNAMIC_TO_BRL = {
    DynamicLevel.PPP: '⠜⠏⠏⠏',
    DynamicLevel.PP: '⠜⠏⠏',
    DynamicLevel.P: '⠜⠏',
    DynamicLevel.MP: '⠜⠍⠏',
    DynamicLevel.MF: '⠜⠍⠋',
    DynamicLevel.F: '⠜⠋',
    DynamicLevel.FF: '⠜⠋⠋',
    DynamicLevel.FFF: '⠜⠋⠋⠋',
    DynamicLevel.SF: '⠜⠎⠋',
    DynamicLevel.SFZ: '⠜⠎⠋⠵',
    DynamicLevel.FP: '⠜⠋⠏',
    DynamicLevel.CRESCENDO_START: '⠜⠉',
    DynamicLevel.DECRESCENDO_START: '⠜⠙',
    DynamicLevel.CRESCENDO_END: '⠜⠒',
    DynamicLevel.DECRESCENDO_END: '⠜⠲',
}


@dataclass
class Dynamic:
    """A dynamic marking."""
    level: DynamicLevel

    def to_lilypond(self) -> str:
        return DYNAMIC_TO_LILYPOND[self.level]

    def to_braille(self) -> str:
        return _DYNAMIC_TO_BRL[self.level]
