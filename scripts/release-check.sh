#!/bin/sh
# release-check.sh: says where the release is up to and what would stop it, changes nothing
# RELEASE_SKIP_STAGES=1 skips build, test, lint and setup, for Jenkins which has just run them.

. "$(dirname "$0")/lib.sh"

check
