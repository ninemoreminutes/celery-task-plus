PYTHON_MAJOR_MINOR := $(shell python -c "import sys; print('{0}{1}'.format(*sys.version_info))")
REQUIREMENTS_TXT = requirements/dev$(PYTHON_MAJOR_MINOR).txt

.PHONY: core-requirements
core-requirements:
	pip install pip setuptools pip-tools

.PHONY: compile-requirements
compile-requirements: core-requirements
	pip install pip setuptools pip-tools
	pip-compile requirements/dev.in -o $(REQUIREMENTS_TXT)

.PHONY: update-requirements
update-requirements: core-requirements
	pip install -U pip setuptools pip-tools
	pip-compile -U requirements/dev.in -o $(REQUIREMENTS_TXT)

.PHONY: requirements
requirements: core-requirements
	pip-sync $(REQUIREMENTS_TXT)

.PHONY: clean-pyc
clean-pyc: requirements
	find . -iname "*.pyc" -delete
	find . -iname __pycache__ | xargs rm -rf

.PHONY: tox-update-requirements
tox-update-requirements: clean-pyc
	tox -c requirements/tox.ini

.PHONY: develop
develop: clean-pyc
	python setup.py develop

.PHONY: check
check: develop
	python manage.py check

.PHONY: migrate
migrate: check
	python manage.py migrate --noinput

.PHONY: clear-cache
clear-cache: check
	python manage.py clear_cache

.PHONY: update-permissions
update-permissions: migrate
	python manage.py update_permissions

.PHONY: runserver
runserver: clear-cache update-permissions migrate
	python manage.py runserver

.PHONY: celery
celery: clear-cache update-permissions migrate
	celery -A test_project worker -E -l DEBUG

.PHONY: beat
beat: clear-cache update-permissions migrate
	celery -A test_project beat -l DEBUG

.PHONY: honcho
honcho: clear-cache update-permissions migrate
	honcho -f Procfile.dev start

.PHONY: honcho-nodeps
honcho-nodeps:
	honcho -f Procfile.dev start

reports:
	mkdir -p $@

.PHONY: pycodestyle
pycodestyle: reports requirements
	set -o pipefail && $@ | tee reports/$@.report

.PHONY: flake8
flake8: reports requirements
	set -o pipefail && $@ | tee reports/$@.report

.PHONY: check8
check8: pycodestyle flake8

.PHONY: test
test: clean-pyc
	python setup.py test

.PHONY: clean-tox
clean-tox:
	rm -rf .tox
	rm -rf .coveragepy*

.PHONY: tox
tox: clean-pyc
	tox

.PHONY: clean-all
clean-all: clean-pyc clean-tox
	rm -rf *.egg-info .eggs .cache .coverage build reports

.PHONY: bump-major
bump-major: requirements
	bumpversion major

.PHONY: bump-minor
bump-minor: requirements
	bumpversion minor

.PHONY: bump-patch
bump-patch: requirements
	bumpversion patch

.PHONY: ship-it
ship-it: requirements clean-pyc
	python setup.py ship_it
