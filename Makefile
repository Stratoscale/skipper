all: build

build:
	python setup.py sdist

install: build
	python setup.py install

clean:
	rm -rf dist *egg-info

.PHONY: build install clean
