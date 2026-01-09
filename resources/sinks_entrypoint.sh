#!/bin/bash
set -e


if [ "${1#-}" != "$1" ]; then
    set -- pulsar-admin sinks localrun "$@"
fi

if [ "$#" -eq 0 ]; then
    set -- pulsar-admin sinks localrun \
        --sink-config-file "$POSTGRES_CONNECTOR_CONFIG_PATH" \
        --broker-service-url "$POSTGRES_CONNECTOR_BROKER_URL"
fi

exec "$@"