#!/bin/bash
set -e

export PULSAR_DATA_DIR="${PULSAR_HOME}/data"

if [ "${1#-}" != "$1" ]; then
    set -- pulsar standalone "$@"
fi

if [ "$#" -eq 0 ]; then
    set -- pulsar standalone
fi

exec "$@"