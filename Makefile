# ---- Config
ACTIVATE_ENV  = . venv/bin/activate
ISORT         = isort src tests 
BLACK         = black src tests 
PYLINT        = pylint src tests 
MYPY          = mypy src

# ---- Dev env
.PHONY: dev
dev:
	python3 -m venv venv
	$(ACTIVATE_ENV) && \
	pip install .[tests,lint,docs,dev] && \
				pip freeze > requirements-lock.txt && \
				pre-commit migrate-config && pre-commit install

.PHONY: fmt
fmt:
	$(ISORT)
		$(BLACK)
	
.PHONY: linting
linting:
	$(ISORT) --check-only -df
		$(BLACK) --check --diff
	$(PYLINT) --enable=w --fail-under=8
	
.PHONY: fmt-lint
fmt-lint: fmt | linting

.PHONY: type-checking
type-checking:
	$(MYPY)

# ---- Documentation
.PHONY: build-docs
build-docs:
	$(ACTIVATE_ENV) && \
	cd docs && \
	sphinx-quickstart \
					--project src \
					--sep \
					--release 0.1.0 \
					--extension 'sphinx.ext.napoleon'
					--makefile
					--no-batchfile

.PHONY: create-docs
create-docs:
	$(ACTIVATE_ENV) && sphinx-apidoc -f -o docs/source src/easy_graphql_server/

# ---- Tests
.PHONY: py-tests
py-tests:
	pytest -s --log-cli-level debug tests/

# ---- Cleanup
.PHONY: cleanup
cleanup:
	rm -rf dist/ build/
