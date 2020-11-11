ACCOUNT=gaf3
IMAGE=relations
INSTALL=python:3.8.5-alpine3.12
VERSION?=0.1
NETWORK=relations.io
MYSQL_IMAGE=mysql/mysql-server:5.7
MYSQL_HOST=$(ACCOUNT)-$(IMAGE)-mysql
POSTGRES_IMAGE=postgres:12.4-alpine
POSTGRES_HOST=$(ACCOUNT)-$(IMAGE)-postgres
DEBUG_PORT=5678
TTY=$(shell if tty -s; then echo "-it"; fi)
VOLUMES=-v ${PWD}/lib:/opt/service/lib \
		-v ${PWD}/test:/opt/service/test \
		-v ${PWD}/mysql.sh:/opt/service/mysql.sh \
		-v ${PWD}/postgres.sh:/opt/service/postgres.sh \
		-v ${PWD}/.pylintrc:/opt/service/.pylintrc \
		-v ${PWD}/setup.py:/opt/service/setup.py
ENVIRONMENT=-e MYSQL_HOST=$(MYSQL_HOST) \
			-e MYSQL_PORT=3306 \
			-e POSTGRES_HOST=$(POSTGRES_HOST) \
			-e POSTGRES_PORT=5432 \
			-e PYTHONDONTWRITEBYTECODE=1 \
			-e PYTHONUNBUFFERED=1 \
			-e test="python -m unittest -v" \
			-e debug="python -m ptvsd --host 0.0.0.0 --port 5678 --wait -m unittest -v"
.PHONY: build network mysql shell debug test lint verify tag untag

build:
	docker build . -t $(ACCOUNT)/$(IMAGE):$(VERSION)

network:
	-docker network create $(NETWORK)

mysql: network
	-docker rm --force $(MYSQL_HOST)
	docker run -d --network=$(NETWORK) -h $(MYSQL_HOST) --name=$(MYSQL_HOST) -e MYSQL_ALLOW_EMPTY_PASSWORD='yes' -e MYSQL_ROOT_HOST='%' $(MYSQL_IMAGE)
	docker run $(TTY) --rm --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "./mysql.sh"

postgres: network
	-docker rm --force $(POSTGRES_HOST)
	docker run -d --network=$(NETWORK) -h $(POSTGRES_HOST) --name=$(POSTGRES_HOST) -e POSTGRES_HOST_AUTH_METHOD='trust' $(POSTGRES_IMAGE)
	docker run $(TTY) --rm --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "./postgres.sh"

shell: mysql postgres
	docker run $(TTY) --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(DEBUG_PORT):5678 $(ACCOUNT)/$(IMAGE):$(VERSION) sh

debug: mysql postgres
	docker run $(TTY) --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) -p 127.0.0.1:$(DEBUG_PORT):5678 $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "python -m ptvsd --host 0.0.0.0 --port 5678 --wait -m unittest discover -v test"

test: mysql postgres
	docker run $(TTY) --network=$(NETWORK) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "coverage run -m unittest discover -v test && coverage report -m --include 'lib/*.py'"

lint:
	docker run $(TTY) $(VOLUMES) $(ENVIRONMENT) $(ACCOUNT)/$(IMAGE):$(VERSION) sh -c "pylint --rcfile=.pylintrc lib/"

verify:
	docker run $(TTY) $(VOLUMES) $(INSTALL) sh -c "cp -r /opt/service /opt/install && cd /opt/install/ && python setup.py install && python -m relations.sql && python -m relations.query && python -m relations.model"

tag:
	-git tag -a "v$(VERSION)" -m "Version $(VERSION)"
	git push origin --tags

untag:
	-git tag -d "v$(VERSION)"
	git push origin ":refs/tags/v$(VERSION)"
