#!/bin/bash
set -euo pipefail

DATASET_SRC="${DATASET_PATH:-/data/datasetcovid.zip}"
TARGET_DIR="/Users/raphaelportela"
TARGET_PATH="${TARGET_DIR}/datasetcovid.zip"

if [ -n "${DATASET_SRC}" ] && [ -f "${DATASET_SRC}" ]; then
    mkdir -p "${TARGET_DIR}"
    ln -sf "${DATASET_SRC}" "${TARGET_PATH}"
else
    echo "❌ Dataset not found at '${DATASET_SRC}'."
    echo "   Mount the zip file into the container, e.g.:"
    echo "   docker run -v /path/to/datasetcovid.zip:${DATASET_SRC} image"
    exit 1
fi

exec "$@"

