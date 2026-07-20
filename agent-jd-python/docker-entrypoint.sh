#!/bin/sh
set -eu

if [ "${IMPORT_SEED_DATA:-true}" = "true" ]; then
    marker="${FAISS_DIR:-/app/data/faiss_index}/.seed-checksum"
    checksum="$(sha256sum /app/seed/knowledge.jsonl | awk '{print $1}')"
    previous=""
    if [ -f "$marker" ]; then
        previous="$(cat "$marker")"
    fi
    if [ "$checksum" != "$previous" ]; then
        echo "Initializing RAG knowledge base..."
        python -m scripts.import_knowledge --file /app/seed/knowledge.jsonl
        printf '%s' "$checksum" > "$marker"
    fi
fi

exec "$@"
