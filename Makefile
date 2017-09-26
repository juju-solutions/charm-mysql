#!/usr/bin/make
PYTHON := /usr/bin/env python
export PYTHONPATH := hooks

virtualenv:
	@if [ ! -d .venv ]; then \
	    virtualenv .venv; \
	    . .venv/bin/activate && \
	    .venv/bin/pip install -U pip; \
	    . .venv/bin/activate && \
	    .venv/bin/pip install -r test-requirements.txt; \
	fi


lint: virtualenv
	@. .venv/bin/activate && \
	    .venv/bin/flake8 --exclude hooks/charmhelpers,tests/charmhelpers \
                hooks unit_tests tests
	@. .venv/bin/activate && .venv/bin/charm-proof

test: virtualenv
	@echo Starting tests...
	@. .venv/bin/activate && \
	    .venv/bin/nosetests --nologcapture --with-coverage unit_tests

functional_test: virtualenv
	@echo Starting Amulet tests...
	@. .venv/bin/activate && \
            .venv/bin/bundletester -vl DEBUG --test-pattern gate-basic-*

bin/charm_helpers_sync.py:
	@mkdir -p bin
	@curl -o bin/charm_helpers_sync.py https://raw.githubusercontent.com/juju/charm-helpers/master/tools/charm_helpers_sync/charm_helpers_sync.py


sync: bin/charm_helpers_sync.py
	$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers.yaml
	$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers-tests.yaml
