# The Descent: Abyssal Leviathan — engine + canvas front end in one container.
#
#   docker compose up -d --build        # http://localhost:8080/canvas
#
# Hardening: slim pinned base, non-root user, no build tools in the final image, read-only root filesystem
# (compose), all Linux capabilities dropped (compose), the debug upload endpoints off unless SLOT_DEBUG_ENDPOINTS=1.

FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ---- dependencies (cached layer) ----
FROM base AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ---- runtime ----
FROM base AS runtime
RUN groupadd --system slot && useradd --system --gid slot --no-create-home --shell /usr/sbin/nologin slot
WORKDIR /app
COPY --from=deps /install /usr/local
# only what the server needs: the engine package (with its static front end) and the math gate for the health of the image
COPY slot_engine/ ./slot_engine/
COPY scripts/math_check.py ./scripts/math_check.py
COPY artifacts/math_baseline.json ./artifacts/math_baseline.json
RUN chown -R root:root /app && chmod -R a-w /app
USER slot
EXPOSE 8080
ENV SLOT_DEBUG_ENDPOINTS=0 \
    SLOT_HOST=0.0.0.0 \
    SLOT_PORT=8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/api/slot/health', timeout=4).status == 200 else 1)"
CMD ["sh", "-c", "python -m uvicorn slot_engine.api.app:app --host ${SLOT_HOST} --port ${SLOT_PORT} --no-server-header --proxy-headers"]
