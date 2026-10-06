#!/bin/sh
# new.sh [+0.0.1|+0.1|+1|x.y.z] [branch name]
# Starts a release. From a clean main that's level with origin: works out the version, makes the branch (gaf3/name,
# or gaf3/version), writes VERSION and the changelog section for it, and commits. VERSION_FILES adds files to the commit.

. "$(dirname "$0")/lib.sh"

spec=${1:-+0.0.1}
name=$2
prefix=${BRANCH_PREFIX:-gaf3}

guard || exit 1

new=$(sh "$(dirname "$0")/version.sh" next "$spec") || exit 1

branch="$prefix/${name:-$new}"

git switch -q -c "$branch" || exit 1

echo "$new" > VERSION

# the changelog gets a dated section: Unreleased becomes it, else it goes above the newest version, else at the end
if ! grep -Eq "^## \[$new\] - [^ ]" CHANGELOG.md; then
    heading="## [$new] - $(date +%F)"
    if grep -q '^## \[Unreleased\]' CHANGELOG.md; then
        awk -v heading="$heading" '!done && /^## \[Unreleased\]/ { print heading; done = 1; next } { print }' CHANGELOG.md > CHANGELOG.md.new
    elif grep -q '^## \[' CHANGELOG.md; then
        awk -v heading="$heading" '!done && /^## \[/ { print heading; print ""; done = 1 } { print }' CHANGELOG.md > CHANGELOG.md.new
    else
        { cat CHANGELOG.md; printf '\n%s\n' "$heading"; } > CHANGELOG.md.new
    fi
    mv CHANGELOG.md.new CHANGELOG.md
fi

# shellcheck disable=SC2086
git add VERSION CHANGELOG.md $VERSION_FILES
git commit -q -m "Version $new"

echo "$branch: $new"
