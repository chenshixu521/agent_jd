#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compose_project="${E2E_COMPOSE_PROJECT_NAME:-agent-jd-e2e}"
web_port="${E2E_WEB_PORT:-3100}"
compose=(docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" -p "$compose_project")

export WEB_PORT="$web_port"
export LLM_PROVIDER=fake
export OPENAI_API_KEY=
export DASHSCOPE_API_KEY=
export FAKE_LLM_DELAY_MS="${FAKE_LLM_DELAY_MS:-350}"
export EMBEDDING_PROVIDER=hash
export EMBEDDING_DIMENSION=384
export JWT_SECRET=e2e-only-jwt-secret-at-least-32-bytes
export AGENT_INTERNAL_TOKEN=e2e-only-shared-internal-token
export MYSQL_ROOT_PASSWORD=e2e-root-password
export MYSQL_DATABASE=agent_jd
export MYSQL_USER=agent_jd_e2e
export MYSQL_PASSWORD=e2e-database-password

cleanup() {
    status=$?
    if [ "$status" -ne 0 ]; then
        mkdir -p "$repo_root/agent-jd-web/test-results"
        "${compose[@]}" logs --no-color \
            > "$repo_root/agent-jd-web/test-results/compose.log" 2>&1 || true
    fi
    "${compose[@]}" down --volumes --remove-orphans || true
}
trap cleanup EXIT

cd "$repo_root"
"${compose[@]}" up -d --build --wait --wait-timeout 600

cd "$repo_root/agent-jd-web"
if [ "${E2E_PLAYWRIGHT_DOCKER:-false}" = "true" ]; then
    docker run --rm --network host --ipc host \
        --user "$(id -u):$(id -g)" \
        --env HOME=/tmp \
        --env "E2E_BASE_URL=http://127.0.0.1:$web_port" \
        --volume "$repo_root/agent-jd-web:/work" \
        --workdir /work \
        mcr.microsoft.com/playwright:v1.61.1-noble \
        npm run test:e2e
else
    E2E_BASE_URL="http://127.0.0.1:$web_port" npm run test:e2e
fi
