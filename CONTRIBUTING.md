# Contributing

## Setup

```bash
git clone https://github.com/oek1ng/zspec.git
cd zspec
uv sync --all-groups --all-extras
pre-commit install
```

## Running checks

```bash
make lint   # ruff + pyrefly
make test   # pytest
make docs   # mkdocs build
```

## Commit convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for PostgreSQL translator
fix: handle empty iterable in all_of
docs: update translator examples
chore: bump dependencies
```

Version bumps and changelog are automated via `python-semantic-release`.

## Pull requests

- Keep changes focused — one feature or fix per PR.
- Ruff and pyrefly must pass.
- Tests must pass.
- Update docs if you change the public API.
