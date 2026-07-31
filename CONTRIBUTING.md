# Contributing to DottedNotes

Thanks for your interest in DottedNotes. This project exists to give blind
composers a direct path from braille music notation to publication-quality
scores and audio, so its own contribution process is held to the same
accessibility bar as the tool itself — see "Accessibility of this
codebase" below.

## Before you start

Please open an issue before starting significant work, so we can coordinate
and avoid duplicated effort. Small, obvious fixes (a typo, a clearly broken
test) don't need an issue first.

## Development environment setup

Follow the "Installation" section of [Readme.md](Readme.md) to install
DottedNotes in a virtual environment with its dev dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The dev dependencies (`pytest`, `pytest-cov`) come from the `[dev]` extra
in `pyproject.toml` — there are no other dev-only tools to install.
LilyPond itself is only needed if you're working on `--compile` or the
formatting-pipeline tests; see Readme.md's "Install LilyPond" section.

## Running the tests

```bash
pytest tests/
pytest tests/ --cov=dottednotes --cov-report=term-missing
```

Run the full suite before opening a PR and after making changes — this
matches how the project is developed day to day (see `CLAUDE.md`'s "How to
Work With This File" section). Tests that invoke the real `lilypond`
binary skip automatically (via `shutil.which("lilypond")`) if it isn't
installed, so a missing LilyPond install won't cause spurious local
failures. CI (`.github/workflows/ci.yml`) runs `pytest tests/
--cov=dottednotes` on Python 3.9 and 3.11 for every push and pull request.

See [docs/development.md](docs/development.md) for the testing
conventions in more depth, including which test file to add to for a
given kind of change and a fixture gotcha (S7-2) that's bitten this
project once already.

## Branch and PR conventions

Branch names should describe the component or feature being worked on
(e.g. `note-class`, `brl-input-pipeline`, matching this repo's own branch
history) rather than being generic (`fix`, `update`). Open pull requests
against `main`. If your change addresses a specific ticket in
`TICKETS.md`, reference its ID (e.g. "S8-3") in the PR description along
with the *why*, not just a restatement of the diff — commit messages in
this repo's history favor a short summary of intent
(`Adds vocal music support...`, `Fixes instrument parsing error...`) over
a list of changed files.

## Code style

There is currently no enforced linter or formatter configured in
`pyproject.toml` — don't introduce one as a drive-by change in an unrelated
PR; propose it as its own issue first, since adding one is a project-wide
decision. In the meantime, match the conventions already used throughout
the codebase: type hints on function signatures, `@dataclass` for domain
model classes, and comments/docstrings that explain *why* something is the
way it is (a cited BANA rule, a specific bug a test is guarding against)
rather than restating what the code already says.

## Accessibility of this codebase

Any change touching CLI output, error messages, or documentation must stay
screen-reader friendly. Concretely, per `CLAUDE.md`'s Developer Context and
the audit performed for ticket S8-1:

- No ASCII art, no progress bars, no color/ANSI-only signaling (anything
  conveyed by color alone with no plain-text equivalent).
- Error messages are plain text and meaningful, never a raw Python
  traceback — see `exceptions.py`'s `DottedNotesError` hierarchy and how
  `cli.py`'s `main()` catches it centrally.
- Documentation avoids tables and diagrams that don't degrade to sensible
  plain text when read linearly (see `docs/development.md` for an example
  of covering the same kind of material as `docs/bana_reference.md`'s
  tables using prose and lists instead).

S8-1 is the concrete bar new PRs are held to, not just a restated abstract
principle — if you're unsure whether a specific piece of output clears it,
say so in the PR description and ask, the same way S8-1 itself required an
actual VoiceOver pass rather than a sighted read-through of the code.

## For blind and low-vision contributors

The primary maintainer works via VoiceOver on macOS with VS Code, and
composes in braille on a BrailleNotetaker device. That's the
known-working setup this section is grounded in — if your own tooling
differs and something below doesn't hold up, please open an issue; this
section is corrected from real reports, not assumed to be complete.

- **Running and reading tests:** `pytest tests/`'s default output is a row
  of `.`/`F` progress characters plus a percentage, which is a visual
  convention that doesn't announce well read live in the terminal.
  Redirect the run to a file instead — `pytest tests/ > output.txt` — and
  open that file to review results; reading a finished, static file is a
  more accessible experience than tracking a scrolling terminal. The
  `--cov-report=term-missing` coverage report is a column-aligned table
  (file path, statement counts, percentage, line numbers), which is a
  genuinely rough spot — there's no non-columnar report format wired up
  in this project yet. If that's a real barrier for you, please say so in
  an issue; it may need a follow-up fix, the same way S8-1 found and
  fixed rough spots in the CLI itself.
- **Reviewing a diff:** GitHub's web PR view is not uniformly accessible
  (large diffs in particular can be hard to navigate). Rather than
  fetching and checking out the PR branch locally — which also goes
  stale once the PR merges and the branch is deleted — append `.diff` to
  the PR's URL in your browser (e.g. `https://github.com/OWNER/REPO/pull/123.diff`)
  to get the whole diff as plain text, then copy it into a text document
  to review. This avoids `git fetch`/checkout entirely.

## BANA accuracy

Braille music dot patterns are never guessed in this codebase. The
authoritative source is `src/dottednotes/bana_symbols.py`; if a symbol you
need isn't already there, cite the *BANA Music Braille Code 2015* manual
(linked from `CLAUDE.md`) or ask the maintainer to confirm the dot pattern
before implementing it. An incorrect dot pattern is a worse outcome than
an honestly unimplemented feature, since it would silently misrepresent
someone's music.

## License

By contributing, you agree your contributions will be licensed under this
project's GPL-3.0 license (see [LICENSE](LICENSE)).
