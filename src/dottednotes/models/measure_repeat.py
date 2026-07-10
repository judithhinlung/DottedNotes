from __future__ import annotations

import copy
import warnings
from dataclasses import dataclass


@dataclass
class MeasureRepeat:
    """Braille full- or part-measure repeat sign (BANA Table 18, Pars.
    18.1-18.4; dots 2,3,5,6).

    The sign may be brailled several times in a row with nothing between
    (BANA 18.2.1 for whole measures, 18.3.1 for part-measures) to mean
    "repeat this material once per sign". `count` is that number of
    occurrences. Whether a given occurrence is a whole- or part-measure
    repeat is a parser-time decision (whole-measure: no notes precede the
    sign in the current measure; part-measure: some do) — this model only
    expands a source item list once that decision has been made.
    """
    count: int
    line: int

    def expand(self, source: list, source_line: int | None = None) -> list:
        """Return `count` deep copies of `source`, concatenated.

        For a part-measure repeat, `source` is the material already written
        before the sign; the caller keeps that original statement and
        appends this method's result for the repetitions. For a
        whole-measure repeat, `source` is the previous measure's notes and
        this method's result *is* the current measure's content (there is
        no original statement in this measure to keep).

        `source_line` is the braille line the original material appeared
        on. BANA 33.4.3 (ensemble/parallel scores) restricts "very obvious"
        repeats to the same braille line as the original passage; when a
        caller supplies it and it differs from `self.line`, this warns
        rather than raising, since that restriction is specific to the
        parallel/ensemble format and not a general BANA rule (Par. 18.1).
        """
        if source_line is not None and source_line != self.line:
            warnings.warn(
                f"Measure repeat sign on braille line {self.line} repeats "
                f"material from line {source_line}, not the same braille "
                "line. BANA 33.4.3 requires 'very obvious' repeats in "
                "ensemble/parallel scores to be on the same line as the "
                "original passage.",
                stacklevel=2,
            )
        expanded: list = []
        for _ in range(self.count):
            expanded.extend(copy.deepcopy(item) for item in source)
        return expanded
