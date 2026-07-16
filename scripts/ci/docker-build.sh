#!/usr/bin/env bash
set -euo pipefail

BACKEND_IMAGE="${BACKEND_IMAGE:-narratwin-ai-backend:ci}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-narratwin-ai-frontend:ci}"

docker build -f backend/Dockerfile -t "${BACKEND_IMAGE}" .
if [[ "${BACKEND_IMAGE}" == "narratwin-ai-backend:ci" ]]; then
  BACKEND_IMAGE=narratwin-ai-backend:ci bash scripts/ci/backend-image-package-check.sh
else
  BACKEND_IMAGE="${BACKEND_IMAGE}" bash scripts/ci/backend-image-package-check.sh
fi
docker build -f frontend/Dockerfile -t "${FRONTEND_IMAGE}" .
