#!/bin/sh
# testpypi-verify.sh: installs the version from testpypi in a clean container and checks it's the one, with pypi for its dependencies.
# The index lags: pip can miss a version curl has already found, so the install is tried again, up to WAIT_TRIES times.

. "$(dirname "$0")/lib.sh"

install() {
    docker run --rm python:3 sh -c "pip install -q --root-user-action=ignore --no-cache-dir --index-url $TESTPYPI_URL/simple/ --extra-index-url https://pypi.org/simple/ $(package)==$(version) && \
python -c \"import importlib.metadata as m; print('installed', m.version('$(package)'))\""
}

retry install
