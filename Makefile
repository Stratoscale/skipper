all: build

build:
	python setup.py sdist

pep8:
	pep8 skipper tests

pylint:
	pylint skipper

tests:
	py.test --cov=skipper --cov-report=term-missing tests

install:
	pip install -U .

uninstall:
	pip uninstall -y strato-skipper

clean:
	rm -rf build dist *egg-info .tox tests/__pycache__
	find -name *.pyc -delete

.PHONY: build pep8 pylint tests install uninstall clean
