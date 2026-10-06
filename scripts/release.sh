#!/bin/sh
# release.sh state|guard|check|release
#   state    how far this version's release is: released, tag-pending, publish-pending or unreleased
#   guard    makes sure we're on a clean main that's level with origin
#   check    says where the release is up to and what would stop it, changes nothing
#   release  from main, does what's left: the checks, testpypi and a clean install from it, pypi, waiting for it, the tag
# RELEASE_SKIP_STAGES=1 skips build, test, lint and setup, for Jenkins which has just run them. RELEASE_TEST=0 skips testpypi.

. "$(dirname "$0")/lib.sh"

# problems: everything that would stop a release
problems() {
    grep -Eq "^## \[$(version)\] - [^ ]" CHANGELOG.md || echo "CHANGELOG.md has no ## [$(version)] - <date> section"
    grep 'git+' requirements.txt | sed 's/^/requirements.txt has a git pin: /'
    sed -En "s/.*['\"]([A-Za-z0-9_.-]+)(>=|==)([0-9][^'\" ,]*)['\"].*/\\1 \\3/p" setup.py | while read -r name floor; do
        curl -sf -o /dev/null "$PYPI_URL/pypi/$name/$floor/json" || echo "$name $floor (the floor in setup.py) isn't published yet"
    done
}

# check: says where the release is up to and what would stop it
check() {
    current=$(state)
    testpypi=no
    published test "$(version)" && testpypi=yes
    echo "$(version): $current (testpypi: $testpypi)"

    if [ "$current" = released ]; then
        echo "nothing to release"
        return 0
    fi

    # a published version has already passed these, all that's left is the tag
    if [ "$current" != tag-pending ]; then
        found=$(problems)
        [ -z "$found" ] || { echo "$found"; return 1; }
        make dist-check || return 1
        [ -n "$RELEASE_SKIP_STAGES" ] || make build test lint setup || return 1
    fi

    echo "ready to release"
}

# release: does what's left, from main
release() {
    guard || return 1

    if [ "$(state)" = released ]; then
        echo "$(version): released, nothing to release"
        return 0
    fi

    check || return 1

    if ! published pypi "$(version)"; then
        if [ "$RELEASE_TEST" != 0 ]; then
            # testpypi takes a version once, so upload only what isn't there, but always check the install before pypi
            published test "$(version)" || make testpypi || return 1
            wait_for test || return 1
            make testpypi-verify || return 1
        fi
        make pypi || return 1
    fi

    wait_for pypi || return 1
    make tag || return 1

    echo "$(package) $(version) released"
}

case "$1" in
    state) state ;;
    guard) guard ;;
    check) check ;;
    release) release ;;
    *) echo "usage: release.sh state|guard|check|release" >&2; exit 2 ;;
esac
