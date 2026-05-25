.PHONY: lint test docs clean

lint:
	uv run ruff check .
	uv run pyrefly check .

test:
	uv run pytest -q

docs:
	uv run mkdocs build -s

clean:
	rm -rf site/ .pytest_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
