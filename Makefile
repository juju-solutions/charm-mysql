#!/usr/bin/make
PYTHON := /usr/bin/env python

virtualenv:
	virtualenv .venv
	.venv/bin/pip install flake8

lint: virtualenv
	.venv/bin/flake8 --exclude hooks/charmhelpers hooks
	@charm proof

# TODO: write some unit tests then uncomment this and the flake8 line above.
#test:
#	@echo Starting tests...
#	@$(PYTHON) /usr/bin/nosetests --nologcapture unit_tests

bin/charm_helpers_sync.py:
	@mkdir -p bin
	@bzr cat lp:charm-helpers/tools/charm_helpers_sync/charm_helpers_sync.py \
        > bin/charm_helpers_sync.py

sync: bin/charm_helpers_sync.py
	$(PYTHON) bin/charm_helpers_sync.py -c charm-helpers.yaml
