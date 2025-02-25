#!/usr/bin/env bash

set -e

if [[ "${CI}" ]]; then
    set -x
fi

if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    python -m tests_v2.test_utils.datasets $@
fi