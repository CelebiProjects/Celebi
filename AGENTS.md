# Repository Guidelines

## Project Structure & Module Organization
- `CelebiChrono/` is the primary Python package (CLI, kernel, and core workflow logic).
- `tests/` contains pytest-based CLI integration tests.
- `UnitTest/` holds legacy/unit-test fixtures and demo data; use as reference data inputs.
- `docs/` and `README.md` provide user-facing documentation.
- `scripts/`, `bin/`, and `tools`-like folders (e.g., `analysis/`, `releaseNote/`) support development and releases.

## Build, Test, and Development Commands
- `pip install .` installs the package locally from source.
- `pip install -e .` installs in editable mode for development.
- `celebi --help` or `celebi-cli --help` verifies CLI entry points.
- `python -m pytest` runs the test suite in `tests/`.

## Coding Style & Naming Conventions
- Python code follows a 100-character line limit (see `.pylintrc`).
- Prefer clear, explicit names for commands and modules; CLI commands use kebab-case (e.g., `add-algorithm`).
- When adding new CLI commands, keep naming consistent with existing `celebi-cli` command patterns.

## Testing Guidelines
- Tests use `pytest` with Click’s `CliRunner` for CLI integration coverage.
- New tests should live in `tests/` and follow `test_*.py` naming.
- Keep tests runnable without requiring an existing Celebi project on disk unless explicitly needed.

## Commit & Pull Request Guidelines
- Commit history shows a mix of conventional prefixes (`feat:`, `chore:`) and plain English subjects.
- Preferred format: short, imperative summaries (e.g., `feat: add runner registry` or `Fix CLI help text`).
- PRs should include a concise description of changes and testing notes (e.g., `python -m pytest`).

## Notes for Contributors
- Primary entry points are defined in `pyproject.toml` under `[project.scripts]`.
- Keep CLI help output stable; it is validated by `tests/test_all_commands_help.py`.
