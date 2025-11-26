# VNEXT

Neutron data reduction software for the VULCAN instrument, at SNS@ORNL

## Getting Started

This project uses [Pixi](https://pixi.sh/) as the single tool for managing environments, dependencies, packaging, and task execution.

### 1. Install Pixi

Follow the installation instructions from the [Pixi website](https://pixi.sh/), or use:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

### 2. Set Up the Environment

Run the following command to create and activate the project environment with all dependencies:

```bash
pixi install
```

### 3. Explore Available Tasks

Use the following command to list all project-defined tasks:

```bash
pixi run
```

Example tasks:

- `build-pypi`: build the PyPI wheel
- `build-conda`: build the Conda package
- `test`: run the test suite
- `conda-publish`, `pypi-publish`: publish the built artifacts
- `clean-*`: clean build artifacts

### 4. Development Workflow

Activate the Pixi environment:

```bash
pixi shell
```

Then, for development:

- Run tests: `pixi run test`
- Run linting: `ruff check .`
- Perform editable install: `pip install --no-deps -e .`

This ensures your environment remains clean and all tasks are reproducible.

## Project Overview

- 📦 **Unified packaging** for both PyPI and Conda via [`pixi build`](https://prefix.dev/docs/pixi/pixi-build/)
- 🐍 **Python 3.11+** compatibility
- ⚙️ **Versioning** handled by [`versioningit`](https://github.com/jwodder/versioningit), derived from Git tags
- 🧪 **Testing** with `pytest` and code coverage reporting
- 🧼 **Linting & formatting** with [`ruff`](https://docs.astral.sh/ruff/)
- 🚀 **Task automation** via `pixi run`
- 🔁 Supports CLI and optional GUI through modular structure in `src/vnext/`


### Known issues

On SNS Analysis systems, the `pixi run conda-build` task will fail due to `sqlite3` file locking issue.
This is most likely due to the user directory being a shared mount,
which interferes with `pixi` and `conda` environment locking.
