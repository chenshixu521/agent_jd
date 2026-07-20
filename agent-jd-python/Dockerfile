FROM python:3.11-slim

ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST} \
    HF_HOME=/models/huggingface \
    TOKENIZERS_PARALLELISM=false

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements-embedding.txt requirements-torch-cpu.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-deps -r requirements-torch-cpu.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -r requirements-embedding.txt

RUN groupadd --system agentjd \
    && useradd --system --gid agentjd --home-dir /app --shell /usr/sbin/nologin agentjd \
    && mkdir -p /app/data/faiss_index /models/huggingface \
    && chown -R agentjd:agentjd /app /models/huggingface

COPY --chown=agentjd:agentjd app ./app
COPY --chown=agentjd:agentjd scripts ./scripts
COPY --chown=agentjd:agentjd seed ./seed
COPY --chown=agentjd:agentjd docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

USER agentjd
EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
