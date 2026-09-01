#!/bin/bash

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    exit 1
fi

PRODUCTION_PATH="${1:-/opt/ane-realtime}"
SOURCE_PATH="${PRODUCTION_PATH}/Plataforma-ANE2"

if [ ! -d "$PRODUCTION_PATH" ]; then
    echo "Error: Production path not found: $PRODUCTION_PATH"
    exit 1
fi

if [ ! -d "$SOURCE_PATH" ]; then
    echo "Error: Source path not found: $SOURCE_PATH"
    exit 1
fi

for component in frontend backend postprocesamiento; do
    source_dir="$SOURCE_PATH/$component"
    target_dir="$PRODUCTION_PATH/$component"

    if [ ! -d "$source_dir" ]; then
        echo "Skipping $component: not found in $SOURCE_PATH"
        continue
    fi

    echo "Copying $component from $source_dir to $target_dir"
    rm -rf "$target_dir"
    cp -r "$source_dir" "$target_dir"
done

echo "Done."
