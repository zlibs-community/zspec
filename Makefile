.PHONY: lint test docs clean

lint:
	uv run ruff check .
	uv run pyrefly check .
	uv run mypy src tests

test:
	uv run pytest -q

coverage:
	uv run pytest -q --cov=zspec --cov-report=term-missing

docs:
	uv run mkdocs build -s

clean:
	rm -rf site/ dist/ .pytest_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
