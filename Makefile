PACKAGE_NAME := strato_skipper

all: lint tests build

build:
	rm -rf build/$(PACKAGE_NAME)-*.whl
	uv build --wheel --out-dir $(PWD)/build/ .
	rm -rf dist *.egg-info build/lib build/bdist*

lint:
	ruff check --preview skipper tests

lint-fix:
	ruff check --preview skipper tests --fix

tests:
	pytest --cov=skipper --cov-report=term-missing -v tests

install:
	uv pip install -U .
	rm -rf dist *.egg-info build/lib build/bdist*

uninstall:
	uv pip uninstall -y strato-skipper

clean:
	rm -rf build dist *egg-info .tox tests/__pycache__ reports
	find -name *.pyc -delete

.PHONY: build lint lint-fix tests install uninstall clean
