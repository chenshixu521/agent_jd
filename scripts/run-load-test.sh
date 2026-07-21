#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compose_project="${LOAD_COMPOSE_PROJECT_NAME:-agent-jd-load}"
web_port="${LOAD_WEB_PORT:-3200}"
locust_binary="${LOCUST_BIN:-}"
compose=(docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" -p "$compose_project")

export WEB_PORT="$web_port"
export LLM_PROVIDER=fake
export OPENAI_API_KEY=
export DASHSCOPE_API_KEY=
export FAKE_LLM_DELAY_MS="${FAKE_LLM_DELAY_MS:-100}"
export EMBEDDING_PROVIDER=hash
export EMBEDDING_DIMENSION=384
export JWT_SECRET=load-only-jwt-secret-at-least-32-bytes
export AGENT_INTERNAL_TOKEN=load-only-shared-internal-token
export MYSQL_ROOT_PASSWORD=load-root-password
export MYSQL_DATABASE=agent_jd
export MYSQL_USER=agent_jd_load
export MYSQL_PASSWORD=load-database-password

cleanup() {
    status=$?
    if [ "$status" -ne 0 ]; then
        mkdir -p "$repo_root/reports"
        "${compose[@]}" logs --no-color > "$repo_root/reports/load-test-compose.log" 2>&1 || true
    fi
    "${compose[@]}" down --volumes --remove-orphans || true
}
trap cleanup EXIT

mkdir -p "$repo_root/reports"
if [ -z "$locust_binary" ] && command -v locust >/dev/null 2>&1; then
    locust_binary="$(command -v locust)"
fi
if [ -z "$locust_binary" ]; then
    load_venv="$repo_root/.load-venv"
    if [ ! -x "$load_venv/bin/locust" ]; then
        python3 -m venv "$load_venv"
        "$load_venv/bin/pip" install -r "$repo_root/load/requirements.txt"
    fi
    locust_binary="$load_venv/bin/locust"
fi
if [ ! -x "$locust_binary" ]; then
    echo "Locust executable is unavailable: $locust_binary" >&2
    exit 1
fi

cd "$repo_root"
"${compose[@]}" up -d --build --wait --wait-timeout 600

users="${LOAD_USERS:-5}"
spawn_rate="${LOAD_SPAWN_RATE:-5}"
duration="${LOAD_DURATION:-30s}"
"$locust_binary" \
    --locustfile "$repo_root/load/locustfile.py" \
    --host "http://127.0.0.1:$web_port" \
    --headless \
    --users "$users" \
    --spawn-rate "$spawn_rate" \
    --run-time "$duration" \
    --stop-timeout 10 \
    --only-summary \
    --csv "$repo_root/reports/load-test" \
    --html "$repo_root/reports/load-test.html" \
    --json \
    > "$repo_root/reports/load-test-summary.json"

python3 "$repo_root/load/render_report.py" \
    "$repo_root/reports/load-test-summary.json" \
    "$repo_root/reports/load-test.md" \
    "$users" \
    "$duration" \
    "$FAKE_LLM_DELAY_MS"
