#!/bin/sh
# changelog-check.sh: fails if CHANGELOG.md has no dated section for the version, changes nothing.
# Just the changelog, so it can run on every branch build: git pins and unpublished floors are for the release to stop.

. "$(dirname "$0")/lib.sh"

found=$(changelog_problem)
[ -z "$found" ] || { echo "$found"; exit 1; }
echo "CHANGELOG.md has ## [$(version)] - <date>"
