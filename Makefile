include .env

native ?= 0

tag ?= ghcr.io/monochromecms/monochrome-api-deta
buildkit ?= 1
test_exit ?= 0
user ?= `id -u`
dir ?= `pwd`

DOCKER_RUN = docker run --env-file .env --rm -v "`pwd`:/vol" -w /vol
DOCKER_TEST_RUN = docker run --env-file .env --rm -e DETA_PROJECT_KEY=$(DETA_PROJECT_KEY) 

.PHONY: help
help: ## Show this help
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker specific commands

.PHONY: build
build:	## Build image
ifeq ($(native),0)
	DOCKER_BUILDKIT=$(buildkit) docker build -t $(tag) .
endif

.PHONY: up
.ONESHELL: up
up start:	## Run a container from the image
ifneq ($(native),0)
	@export `grep -v '^#' .env | xargs -d '\n'`
	hypercorn main:app -b 0.0.0.0:3000 --reload
else
	docker run --rm -ti --name monochrome-api -p 3000:3000 --env-file .env $(tag)
endif

.PHONY: logs
logs:	## Read the container's logs
	docker logs -f --tail 500 monochrome-api

.PHONY: sh
sh: ## Open a shell in the running container
	docker -ti exec monochrome-api sh

# Dev utils

.PHONY: lock
.ONESHELL: lock
lock:	## Refresh pipfile.lock
ifneq ($(native),0)
	cd api
	pipenv lock --pre
else
	$(DOCKER_RUN) $(tag) pipenv lock --pre
endif

.PHONY: lint
lint:  ## Lint project code
ifneq ($(native),0)
	black ./api --check --diff
	flake8 ./api
else
ifneq ($(test_exit),0)
	$(DOCKER_RUN) $(tag) lint
else
	-$(DOCKER_RUN) $(tag) lint
endif
endif

.PHONY: format
format:  ## Format project code
ifneq ($(native),0)
	black ./api
else
	$(DOCKER_RUN) $(tag) format
endif

.PHONY: secret
secret: ## Generate a secret
	@openssl rand -hex 30

.PHONY: create_admin
.ONESHELL: create_admin
create_admin: ## Create a new admin user
ifneq ($(native),0)
	python ./api/create_admin.py
else
	$(DOCKER_RUN) -ti $(tag) create_admin
endif

# TESTING

.PHONY: _test_setup
.ONESHELL: _test_setup
_test_setup: build
	@echo Adding the default user...
	@$(DOCKER_TEST_RUN) -e MONOCHROME_TEST=1 $(tag) create_admin

.PHONY: _test
_test:
	@echo Running backend tests...
ifeq ($(test_exit),1)
	$(DOCKER_TEST_RUN) $(tag) python -m pytest --cov api --cov-config=/api/setup.cfg -v api
else
	-$(DOCKER_TEST_RUN) -v "`pwd`/htmlcov:/html" $(tag) python -m pytest --cov api --cov-report html:/html --cov-config=/api/setup.cfg -v api
endif

test: lint _test ## Run the tests
