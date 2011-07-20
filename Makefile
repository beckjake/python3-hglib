PYTHON=python
help:
	@echo 'Commonly used make targets:'
	@echo '  tests - run all tests in the automatic test suite'

all: help

.PHONY: tests

tests:
	cd tests && $(PYTHON) $(HGREPO)/tests/run-tests.py -l $(TESTFLAGS)
