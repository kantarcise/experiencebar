# experiencebar

`experiencebar` is a terminal MMORPG-style XP bar for gamifying work. Run it while
you work and it awards experience over time, persists progress between sessions,
and levels you up when your current-level XP reaches the next threshold.

State is stored as a small JSON file, so there is no database to install or run.

## Install

This project uses `uv` for environment and dependency management.

You need:

- Python 3.11 or newer
- `uv`

From this repository, install the project environment:

```bash
uv sync
```

## Quick Start

Start earning XP while you work:

```bash
uv run experiencebar
```

The bar shows progress inside the current level, not lifetime XP:

```text
Level 12 | XP 3400/5000 | 68%
```

Stop with `Ctrl+C`; progress is saved automatically.

Check your saved progress later:

```bash
uv run experiencebar status
```

## Commands

Show current progress:

```bash
uv run experiencebar status
```

Run a timed work session:

```bash
uv run experiencebar work --minutes 25
```

Award XP manually:

```bash
uv run experiencebar gain 50 --reason "finished review"
```

Create difficulty-based tasks:

```bash
uv run experiencebar task add "Write proposal" hard
uv run experiencebar task list
uv run experiencebar task complete 1
```

Task difficulties award:

| Difficulty | XP |
| --- | ---: |
| trivial | 10 |
| easy | 25 |
| medium | 60 |
| hard | 120 |
| epic | 250 |

Reset progress:

```bash
uv run experiencebar reset
```

## State file

By default, state lives at:

```text
~/.local/state/experiencebar/state.json
```

If `XDG_STATE_HOME` is set, that directory is used instead. You can override the
state location per command:

```bash
uv run experiencebar --state-file ./my-xp.json status
```

## Development

Run tests and linting with `uv`:

```bash
uv run python -m unittest discover -s tests
uv run ruff check .
uv run ruff format --check .
```

## XP curve

Each level requires more XP than the last:

```text
xp_needed = 100 + (level - 1) * 50 + floor((level - 1) ** 1.6 * 20)
```

The displayed percentage is:

```text
current XP in this level / XP required for next level
```
