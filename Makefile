.PHONY: setup test test-quick lint typecheck check schemas fixtures

setup:      ## install Python 3.12 + deps
	uv sync

test:
	uv run pytest -q

test-quick:  ## while iterating: stop at the first failure, one line per failure (make test-quick T=tests/test_x.py)
	uv run pytest -q -x --tb=line $(T)

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy lens create

check: lint typecheck test  ## everything CI runs
	uv run lens dag --check
	uv run lens validate --all
	uv run lens schemas export --check

schemas:
	uv run lens schemas export

fixtures:   ## synthetic fixture videos (gitignored)
	uv run python scripts/make_fixtures.py
