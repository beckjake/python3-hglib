PYTHON=python
help:
	@echo 'Commonly used make targets:'
	@echo '  tests - run all tests in the automatic test suite'

all: help

.PHONY: tests

tests:
	$(PYTHON) test.py --with-doctest
