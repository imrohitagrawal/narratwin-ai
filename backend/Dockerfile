FROM docker.io/library/python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0 AS cpython-backports

COPY security/cpython-3.13.14/ /tmp/cpython-backports/
COPY scripts/ci/verify-cpython-backports.py /tmp/verify-cpython-backports.py
RUN python /tmp/cpython-backports/apply_backports.py \
      --root /usr/local/lib/python3.13 \
      --manifest /tmp/cpython-backports/backports.json \
    && python /tmp/verify-cpython-backports.py --expect fixed --max-seconds 2

FROM docker.io/library/python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0

COPY --from=cpython-backports /usr/local/lib/python3.13/tarfile.py /usr/local/lib/python3.13/tarfile.py
COPY --from=cpython-backports /usr/local/lib/python3.13/html/parser.py /usr/local/lib/python3.13/html/parser.py

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=container

WORKDIR /app

RUN python -m pip install --no-cache-dir uv==0.11.18

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend ./backend
RUN adduser -D -u 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD [".venv/bin/uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
