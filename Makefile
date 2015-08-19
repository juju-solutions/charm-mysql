#!/usr/bin/make
PYTHON := /usr/bin/env python
export PYTHONPATH := hooks

virtualenv:
	virtualenv .venv
	.venv/bin/pip install flake8 nose coverage mock six pyyaml \
        netifaces netaddr

lint: virtualenv
	.venv/bin/flake8 --exclude hooks/charmhelpers,tests/charmhelpers \
        hooks unit_tests tests
	@charm proof

test: virtualenv
	@echo Starting tests...
	@.venv/bin/nosetests --nologcapture --with-coverage unit_tests

functional_test:
	@echo Starting Amulet tests...
	@juju test -v -p AMULET_HTTP_PROXY,AMULET_OS_VIP --timeout 2700

bin/charm_helpers_sync.py:
	@mkdir -p bin
	@bzr cat lp:charm-helpers/tools/charm_helpers_sync/charm_helpers_sync.py \
        > bin/charm_helpers_sync.py

sync: bin/charm_helpers_sync.py
	$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers.yaml
	$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers-tests.yaml
