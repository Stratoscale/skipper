all: build

build:
	python setup.py sdist

pep8:
	pep8 skipper tests

tests:
	py.test tests

install: build
	python setup.py install

clean:
	rm -rf dist *egg-info

.PHONY: build tests install clean
