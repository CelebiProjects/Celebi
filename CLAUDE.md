# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Celebi is a data analysis management toolkit for high-energy physics research. It provides structured organization for projects, tasks, algorithms, and data with dependency tracking, versioning (impressions), and reproducible workflows.

## Development Commands

### Installation and Setup
```bash
# Install in development mode
pip install -e .

# Build package
python -m build

# Install from built wheel
pip install dist/chern-0.0.1-py3-none-any.whl
```

### Testing
```bash
# Run unit tests (from project root)
cd UnitTest
python -m pytest -v

# Run specific test file
python -m pytest test_vtask.py -v

# Run tests from project root (alternative)
python -m pytest UnitTest/ -v
```

### Linting
```bash
# Run pylint on CelebiChrono package
python -m pylint $(git ls-files "CelebiChrono/*.py") --disable="fixme,too-many-ancestors,broad-exception-raised"
```

### Documentation
```bash
# Build documentation (requires sphinx)
cd docs
make html
```

## Architecture Overview

### Core Components

**CelebiChrono** - Main package containing:
- `kernel/` - Core object models and business logic
  - `vobject.py` - Base virtual object class
  - `vproject.py` - Project management
  - `vtask.py`, `vtask_job.py` - Task execution and job management
  - `valgorithm.py` - Algorithm definitions
  - `vimpression.py` - Versioning/snapshot system
  - `chern_communicator.py` - Communication layer
- `interface/` - User interfaces
  - `chern_shell/` - Interactive shell commands
  - `shell.py` - Shell interface
- `utils/` - Utility functions
  - `file_utils.py`, `path_utils.py` - File/path operations
  - `metadata.py` - Configuration management
  - `container_manager.py` - Docker container management
- `celebi_cli/` - Command-line interface
- `main.py` - Entry point with Click CLI

### Key Architectural Patterns

1. **Virtual Object Hierarchy**: All entities (projects, tasks, data, algorithms) inherit from `VObject` base class
2. **DAG-based Dependency Tracking**: Tasks form directed acyclic graphs with automatic dependency resolution
3. **Impressions System**: Versioning mechanism for capturing analysis states over time
4. **Runner Abstraction**: Execution backends (local, batch, remote) abstracted through runner interfaces
5. **Metadata Management**: Two-tier metadata system (human-readable YAML and machine JSON)

### Development Patterns

- **Testing**: Uses `unittest` framework with mocks. Tests are in `UnitTest/` directory
- **CLI**: Built with Click framework. Main entry point is `CelebiChrono.main:main`
- **Interactive Shell**: Custom shell implementation in `interface/chern_shell/`
- **Configuration**: User config stored in `~/.celebi/`, project config in project directories

### Important File Locations

- **Entry Points**: `CelebiChrono/main.py` (CLI), `CelebiChrono/interface/shell.py` (interactive)
- **Core Models**: `CelebiChrono/kernel/v*.py` files
- **Utilities**: `CelebiChrono/utils/*.py`
- **Tests**: `UnitTest/test_*.py`
- **Documentation**: `docs/` directory with Sphinx
- **Scripts**: `scripts/` for development utilities
- **External Tools**: `externel/` for third-party integrations

## Workflow Notes

1. **Project Structure**: Celebi manages projects with specific directory layouts containing `tasks/`, `data/`, `algorithms/` subdirectories
2. **First-time Setup**: Creates `~/.celebi/` config directory on first run
3. **Development Environment**: Use `bin/thischern.sh` to set up local development environment
4. **CI/CD**: GitHub Actions run tests on Python 3.9-3.13 and pylint checks

## Common Development Tasks

When adding new features:
1. Add core model in `CelebiChrono/kernel/`
2. Add CLI command in `CelebiChrono/main.py` or shell command in `interface/chern_shell/`
3. Add tests in `UnitTest/`
4. Update documentation in `docs/` if needed

When debugging:
- Check `~/.celebi/logs/` for application logs
- Use interactive shell for testing: `celebi` command
- Examine metadata files in project directories (YAML and JSON)