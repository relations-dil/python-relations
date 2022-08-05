ACCOUNT=gaf3
IMAGE=python-relations
INSTALL=python:3.8.5-alpine3.12
VERSION?=0.6.11
DEBUG_PORT=5678
TTY=$(shell if tty -s; then echo "-it"; fi)
VOLUMES=-v ${PWD}/lib:/opt/service/lib \
		-v ${PWD}/test:/opt/service/test \
		-v ${PWD}/.pylintrc:/opt/service/.pylintrc \
		-v ${PWD}/setup.py:/opt/service/setup.py
ENVIRONMENT=-e PYTHONDONTWRITEBYTECODE=1 \
			-e PYTHONUNBUFFERED=1 \
			-e test="python -m unittest -v" \
			-e debug="python -m ptvsd --host 0.0.0.0 --port 5678 --wait -m unittest -v"
PYPI=-v ${PWD}/LICENSE.txt:/opt/service/LICENSE.txt \
	-v ${PWD}/PYPI.md:/opt/service/README.md \
	-v ${HOME}/.pypirc:/opt/service/.pypirc

.PHONY: build shell debug test lint setup tag untag

build:
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

shell:
	docker run $(TTY) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(DEBUG_PORT):5678 $(ACCOUNT)/$(IMAGE):$(VERSION) sh

debug:
	docker run $(TTY) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(DEBUG_PORT):5678 $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "python -m ptvsd --host 0.0.0.0 --port 5678 --wait -m unittest discover -v test"

test:
	docker run $(TTY) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "coverage run -m unittest discover -v test && coverage report -m --include 'lib/*.py'"

lint:
	docker run $(TTY) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "pylint --rcfile=.pylintrc lib/"

setup:
	docker run $(TTY) $(VOLUMES) $(PYPI) $(INSTALL) sh -c "cp -r /opt/service /opt/install && cd /opt/install/ && \
	python setup.py install && \
	python -m relations.source && \
	python -m relations.unittest && \
	python -m relations.field && \
	python -m relations.titles && \
	python -m relations.model && \
	python -m relations.record && \
	python -m relations.relation && \
	python -m relations.migrations"

tag:
	-git tag -a $(VERSION) -m "Version $(VERSION)"
	git push origin --tags

untag:
	-git tag -d $(VERSION)
	git push origin ":refs/tags/$(VERSION)

testpypi:
	docker run $(TTY) $(VOLUMES) $(PYPI) gaf3/pypi sh -c "cd /opt/service && \
	python -m build && \
	python -m twine upload -r testpypi --config-file=.pypirc dist/*"

pypi:
	docker run $(TTY) $(VOLUMES) $(PYPI) gaf3/pypi sh -c "cd /opt/service && \
	python -m build && \
	python -m twine upload --config-file=.pypirc dist/*"
