all: build

build:
	python setup.py sdist

pep8:
	pep8 skipper tests

pylint:
	pylint skipper

tests:
	py.test --cov=skipper tests

install: build
	python setup.py install

clean:
	rm -rf dist *egg-info

.PHONY: build pep8 pylint tests install clean
