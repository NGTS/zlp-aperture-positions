#!/usr/bin/env bash

set -e

main() {
    local readonly dir=$1
    shift
    local readonly args=$@

    python ${PWD}/visualise_apertures.py ${dir} -p ${dir} ${args}
}

main "$@"
