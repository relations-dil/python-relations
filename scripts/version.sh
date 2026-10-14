#!/bin/sh
# version.sh next|write [+0.0.1|+0.1|+1|x.y.z]
# The next version from VERSION and a bump (+1, +0.1 or +0.0.1: raise that place, zero what's after it) or a version
# outright. It has to be x.y.z, has to increase, and can't be published already. write also writes VERSION.

. "$(dirname "$0")/lib.sh"

mode=${1:-next}
spec=${2:-+0.0.1}
current=$(version)

fail() {
    echo "$1" >&2
    exit 1
}

echo "$current" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || fail "VERSION $current is not x.y.z"

case "$spec" in
    +*)
        echo "$spec" | grep -Eq '^\+[0-9]+(\.[0-9]+){0,2}$' || fail "$spec is not a bump like +1, +0.1 or +0.0.1"
        new=$(echo "$current $spec" | awk '
            {
                split($1, current, ".")
                count = split(substr($2, 2), amounts, ".")
                for (place = count + 1; place <= 3; place++) amounts[place] = 0
                for (place = 1; place <= 3; place++) if (amounts[place] + 0 > 0) { raised = place; changed++ }
                if (changed != 1) exit 1
                current[raised] += amounts[raised]
                for (place = raised + 1; place <= 3; place++) current[place] = 0
                print current[1] "." current[2] "." current[3]
            }') || fail "$spec is not a bump like +1, +0.1 or +0.0.1"
        ;;
    *) new=$spec ;;
esac

echo "$new" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || fail "$new is not x.y.z"

echo "$current $new" | awk '
    {
        split($1, a, ".")
        split($2, b, ".")
        for (i = 1; i <= 3; i++) {
            if (b[i] + 0 > a[i] + 0) exit 0
            if (b[i] + 0 < a[i] + 0) exit 1
        }
        exit 1
    }' || fail "$new does not increase $current"

! listed pypi "$new" || fail "$(package) $new is already published"

[ "$mode" = write ] && echo "$new" > VERSION

echo "$new"
