#!/bin/sh
# release.sh: from main, does what's left of the release: the checks, testpypi and a clean install from it, pypi, waiting for it, the tag
# RELEASE_TEST=0 skips testpypi.

. "$(dirname "$0")/lib.sh"

# release: does what's left, from main
release() {
    guard || return 1

    if [ "$(state)" = released ]; then
        echo "$(version): released, nothing to release"
        return 0
    fi

    check || return 1

    if ! listed pypi "$(version)"; then
        if [ "$RELEASE_TEST" != 0 ]; then
            # testpypi takes a version once, so upload only what isn't there, but always check the install before pypi
            listed test "$(version)" || make testpypi || return 1
            wait_for test || return 1
            make testpypi-verify || return 1
        fi
        make pypi || return 1
    fi

    wait_for pypi || return 1
    make tag || return 1

    echo "$(package) $(version) released"
}

release
