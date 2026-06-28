# Test Fixtures

This directory holds `.brf` and `.brl` braille music files used as test inputs.

| File | Title | Composer | Source |
|------|-------|----------|--------|
| fengyang_flower_drum.brf | Fengyang Flower Drum (凤阳花鼓) | Traditional Chinese folk song | Developer-authored (Judith Lung) |

## Notes

- `fengyang_flower_drum.brf` is the primary integration test fixture.
  The developer composed it and knows the expected LilyPond output exactly.
  It is the most reliable ground-truth test case in the suite.
- Additional public-domain fixtures (NLS, RNIB) to be added in S0-6.
