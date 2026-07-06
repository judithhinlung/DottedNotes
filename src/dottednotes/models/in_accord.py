from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InAccord:
    """Two or more independent rhythmic lines written within one braille measure.

    BANA Chapter 11.  Each element of `parts` is one voice — a list of Note or
    Chord objects.  The voice order follows BANA convention: for treble/alto clef,
    highest voice first; for bass/tenor clef, lowest voice first.

    in_accord_type values:
        'full_measure'      — full-measure in-accord (BANA 11.1.1): each part fills a whole measure.
        'part_measure'      — part-measure in-accord (BANA 11.1.2): each part fills one temporal
                              section of a measure; sections are concatenated by the caller.
    """

    parts: list[list] = field(default_factory=list)
    in_accord_type: str = 'full_measure'

    def to_relative_lilypond(self, prev_midi: int) -> tuple[str, int]:
        """Render as LilyPond simultaneous voices.

        Each voice resets to `prev_midi` as its relative-mode reference
        (LilyPond behaviour: each `{ }` inside `<< >>` inherits the reference
        from before the block).  After `>>`, the reference advances to the last
        note of `parts[0]` (the primary voice), matching LilyPond's own rule.

        Returns (lilypond_str, new_prev_midi).
        """
        voice_strs: list[str] = []
        last_midi = prev_midi

        for idx, part in enumerate(self.parts):
            cur_midi = prev_midi  # each voice starts from the same reference
            note_strs: list[str] = []
            for item in part:
                if hasattr(item, 'to_relative_lilypond'):
                    s, cur_midi = item.to_relative_lilypond(cur_midi)
                else:
                    s = item.to_lilypond()
                note_strs.append(s)
            voice_strs.append('{ ' + ' '.join(note_strs) + ' }')
            if idx == 0:
                last_midi = cur_midi  # primary voice sets the post-block reference

        return '<< ' + ' \\\\ '.join(voice_strs) + ' >>', last_midi
