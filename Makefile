.PHONY: setup verify test lint format

setup:
	pip install -e .[dev]
	pre-commit install

verify:
	PYTHONUTF8=1 python -m engine.cli verify --target models

test:
	PYTHONUTF8=1 python -m pytest tests/ -v --tb=short

lint:
	ruff check engine/ tests/
	mypy engine/ --ignore-missing-imports

format:
	ruff format engine/ tests/

spike:
	PYTHONUTF8=1 python -m engine.cli spike

plan:
	PYTHONUTF8=1 python -m engine.cli plan --corpus-size 10000

collect:
	PYTHONUTF8=1 python -m engine.cli collect
