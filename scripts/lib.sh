# shellcheck shell=sh
# Shared by the release scripts, source it: . "$(dirname "$0")/lib.sh"
# PYPI_URL, TESTPYPI_URL, WAIT_TRIES and WAIT_DELAY can be set to point at other registries or wait less or longer.

PYPI_URL=${PYPI_URL:-https://pypi.org}
TESTPYPI_URL=${TESTPYPI_URL:-https://test.pypi.org}
WAIT_TRIES=${WAIT_TRIES:-180}
WAIT_DELAY=${WAIT_DELAY:-10}

# the name on pypi, and the version being worked on
package() {
    grep -m1 'name=' setup.py | cut -d'"' -f2
}

version() {
    cat VERSION
}

# listed pypi|test version [name]: whether the simple index, what pip reads, lists the version of the package (or another), it lags
listed() {
    case "$1" in
        test) base=$TESTPYPI_URL ;;
        *) base=$PYPI_URL ;;
    esac
    curl -sfL "$base/simple/${3:-$(package)}/" | grep -Eq -- "[-_]$(echo "$2" | sed 's/\./\\./g')(\.tar\.gz|-py)"
}

# wait_for pypi|test: waits for the version to show up on the index, it lags for minutes after an upload
wait_for() {
    tries=0
    while [ "$tries" -lt "$WAIT_TRIES" ]; do
        if listed "$1" "$(version)"; then
            echo "$(package) $(version) is on $1"
            return 0
        fi
        tries=$((tries + 1))
        [ "$tries" -lt "$WAIT_TRIES" ] && sleep "$WAIT_DELAY"
    done
    echo "$(package) $(version) is not on $1" >&2
    return 1
}

# retry command...: runs the command until it works, WAIT_TRIES times, WAIT_DELAY apart. What pip sees of an index
# lags what curl sees of it, so a clean install right after wait_for may miss a version that is there.
retry() {
    tries=0
    while [ "$tries" -lt "$WAIT_TRIES" ]; do
        "$@" && return 0
        tries=$((tries + 1))
        [ "$tries" -lt "$WAIT_TRIES" ] && sleep "$WAIT_DELAY"
    done
    echo "gave up on: $*" >&2
    return 1
}

# guard: makes sure we're on a clean main that's level with origin.
guard() {
    git fetch -q origin
    branch=$(git rev-parse --abbrev-ref HEAD)
    [ "$branch" = main ] || { echo "not on main (on ${branch:-no branch})"; return 1; }
    [ -z "$(git status --porcelain)" ] || { echo "the working tree isn't clean"; return 1; }
    [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "main isn't level with origin/main"; return 1; }
}

# state: how far the release of this version is: released, tag-pending, publish-pending or unreleased
state() {
    tagged=no
    git ls-remote --exit-code --tags origin "$(version)" > /dev/null 2>&1 && tagged=yes
    live=no
    listed pypi "$(version)" && live=yes
    case "$tagged$live" in
        yesyes) echo released ;;
        noyes) echo tag-pending ;;
        yesno) echo publish-pending ;;
        *) echo unreleased ;;
    esac
}

# problems: everything that would stop a release
problems() {
    grep -Eq "^## \[$(version)\] - [^ ]" CHANGELOG.md || echo "CHANGELOG.md has no ## [$(version)] - <date> section"
    grep 'git+' requirements.txt | sed 's/^/requirements.txt has a git pin: /'
    sed -En "s/.*['\"]([A-Za-z0-9_.-]+)(>=|==)([0-9][^'\" ,]*)['\"].*/\\1 \\3/p" setup.py | while read -r name floor; do
        listed pypi "$floor" "$name" || echo "$name $floor (the floor in setup.py) isn't published yet"
    done
}

# check: says where the release is up to and what would stop it
check() {
    current=$(state)
    testpypi=no
    listed test "$(version)" && testpypi=yes
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
    fi

    echo "ready to release"
}
