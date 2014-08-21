#!/usr/bin/env bash

set -e

main() {
    local readonly dir=$1
    shift
    local readonly args=$@

    if [[ "${dir}" == "-h" || "${dir}" == "--help" ]]; then
        python ${PWD}/visualise_apertures.py -h
    else
        python ${PWD}/visualise_apertures.py ${dir} -p ${dir} ${args}
    fi
}

main "$@"
