from pathlib import Path
from typing import Union


class InputPipeline:
    """Reads and pre-processes braille music files before parsing."""

    def __init__(self, path: Union[str, Path]) -> None:
        self.path = Path(path)

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")

    def lines(self) -> list[str]:
        return self.read().splitlines()
