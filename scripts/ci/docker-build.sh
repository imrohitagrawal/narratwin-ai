#!/usr/bin/env bash
set -euo pipefail

BACKEND_IMAGE="${BACKEND_IMAGE:-narratwin-ai-backend:ci}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-narratwin-ai-frontend:ci}"

docker build -f backend/Dockerfile -t "${BACKEND_IMAGE}" .
BACKEND_IMAGE="${BACKEND_IMAGE}" bash scripts/ci/backend-image-package-check.sh
docker build -f frontend/Dockerfile -t "${FRONTEND_IMAGE}" .
