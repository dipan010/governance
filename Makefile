BACKEND_PY := backend/.venv/bin/python

.PHONY: backend-lint backend-typecheck backend-test \
        frontend-lint frontend-typecheck frontend-test build \
        acceptance all

backend-lint:
	cd backend && .venv/bin/ruff format --check . && .venv/bin/ruff check .

backend-typecheck:
	cd backend && .venv/bin/mypy app tests

backend-test:
	cd backend && .venv/bin/pytest -q

frontend-lint:
	cd frontend && npm run lint

frontend-typecheck:
	cd frontend && npm run typecheck

frontend-test:
	cd frontend && npm test

build:
	cd frontend && npm run build

acceptance:
	$(BACKEND_PY) scripts/validate_acceptance.py

all: backend-lint backend-typecheck backend-test \
     frontend-lint frontend-typecheck frontend-test build acceptance
