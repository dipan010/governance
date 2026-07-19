VENV ?= .venv
PY := $(VENV)/bin/python
UV ?= uv

.PHONY: install format lint typecheck test run

install:
	$(UV) venv -p 3.12 $(VENV)
	$(UV) pip install -p $(PY) -e ".[dev]"

format:
	$(PY) -m ruff format .

lint:
	$(PY) -m ruff format --check .
	$(PY) -m ruff check .

typecheck:
	$(PY) -m mypy app tests

test:
	$(PY) -m pytest

run:
	$(PY) -m uvicorn app.main:app --reload --port 8000
