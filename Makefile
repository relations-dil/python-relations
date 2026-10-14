ACCOUNT=gaf3
IMAGE=python-relations
INSTALL=python:3.8.5-alpine3.12
VERSION?=$(shell cat VERSION)
DEBUG_PORT=5678
TTY=$(shell if tty -s; then echo "-it"; fi)
VOLUMES=-v ${PWD}/lib:/opt/service/lib \
		-v ${PWD}/test:/opt/service/test \
		-v ${PWD}/.pylintrc:/opt/service/.pylintrc \
		-v ${PWD}/VERSION:/opt/service/VERSION \
		-v ${PWD}/setup.py:/opt/service/setup.py
ENVIRONMENT=-e PYTHONDONTWRITEBYTECODE=1 \
			-e PYTHONUNBUFFERED=1 \
			-e test="python -m unittest -v" \
			-e debug="python -m ptvsd --host 0.0.0.0 --port 5678 --wait -m unittest -v"
PYPI=-v ${PWD}/LICENSE.txt:/opt/service/LICENSE.txt \
	-v ${PWD}/PYPI.md:/opt/service/README.md \
	-v ${HOME}/.pypirc:/opt/service/.pypirc

.PHONY: build shell debug test lint setup tag untag testpypi pypi new version release-check release dist-check testpypi-verify test-release help
.DEFAULT_GOAL := help

build: ## Builds the docker image
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

shell: ## Opens a shell in the container
	docker run --rm $(TTY) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(DEBUG_PORT):5678 $(ACCOUNT)/$(IMAGE):$(VERSION) sh

debug: ## Runs the tests under the debugger on port 5678
	docker run --rm $(TTY) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(DEBUG_PORT):5678 $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "python -m ptvsd --host 0.0.0.0 --port 5678 --wait -m unittest discover -v test"

test: ## Runs the tests with coverage
	docker run --rm $(TTY) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "coverage run -m unittest discover -v test && coverage report -m --include 'lib/*.py'"

lint: ## Runs pylint
	docker run --rm $(TTY) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "pylint --rcfile=.pylintrc lib/"

setup: ## Checks it installs and its modules run on the oldest python
	docker run --rm $(TTY) $(VOLUMES) $(PYPI) $(INSTALL) sh -c "cp -r /opt/service /opt/install && cd /opt/install/ && \
	python setup.py install && \
	python -m relations.error && \
	python -m relations.source && \
	python -m relations.unittest && \
	python -m relations.field && \
	python -m relations.titles && \
	python -m relations.model && \
	python -m relations.record && \
	python -m relations.relation && \
	python -m relations.migrations"

tag: ## Tags the version and pushes the tag
	-git tag -a $(VERSION) -m "Version $(VERSION)"
	git push origin --tags

untag: ## Removes the version's tag
	-git tag -d $(VERSION)
	git push origin ":refs/tags/$(VERSION)"

testpypi: ## Uploads the version to TestPyPI
	docker run --rm $(TTY) $(VOLUMES) $(PYPI) python:3 sh -c "pip install -q --root-user-action=ignore build twine && cd /opt/service && \
	BUILD_VERSION='$(VERSION)' python -m build && \
	python -m twine upload -r testpypi --config-file=.pypirc dist/*"

pypi: ## Uploads the version to PyPI
	docker run --rm $(TTY) $(VOLUMES) $(PYPI) python:3 sh -c "pip install -q --root-user-action=ignore build twine && cd /opt/service && \
	BUILD_VERSION='$(VERSION)' python -m build && \
	python -m twine upload --config-file=.pypirc dist/*"

# Releases: make new starts one, make release-check says where it's up to and what would stop it, make release finishes it.
# V is +0.0.1 (the default), +0.1, +1 or a version outright, and B names the branch. The work is in scripts/.
V?=+0.0.1
B?=

new: ## Starts a release: next version, branch, VERSION, changelog (V=+0.0.1|+0.1|+1|x.y.z, B=name)
	@sh scripts/new.sh "$(V)" "$(B)"

version: ## Sets VERSION (V=+0.0.1|+0.1|+1|x.y.z)
	@sh scripts/version.sh write "$(V)"

release-check: ## Says where the release is up to and what would stop it
	@sh scripts/release-check.sh

release: ## Does what's left of the release: checks, TestPyPI, PyPI, the tag
	@sh scripts/release.sh

dist-check: ## Builds the distributions and runs twine check
	docker run --rm $(TTY) $(VOLUMES) $(PYPI) python:3 sh -c "pip install -q --root-user-action=ignore build twine && cd /opt/service && \
	BUILD_VERSION='$(VERSION)' python -m build && \
	python -m twine check dist/*"

testpypi-verify: ## Installs the version from TestPyPI in a clean container
	@sh scripts/testpypi-verify.sh

# Tests the release scripts against a throwaway repo and fake indexes, nothing real is touched
test-release: ## Tests the release scripts against a throwaway repo and fake indexes
	docker run --rm $(TTY) -v ${PWD}/scripts:/opt/scripts python:3 sh /opt/scripts/test-release.sh

help: ## Lists the targets
	@awk -F ':.*## ' '/^[a-z-]+:.*## /{printf "%-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
