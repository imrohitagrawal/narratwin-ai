#!/usr/bin/env bash
set -euo pipefail

docker build -f backend/Dockerfile -t narratwin-ai-backend:ci .
BACKEND_IMAGE=narratwin-ai-backend:ci bash scripts/ci/backend-image-package-check.sh
docker build -f frontend/Dockerfile -t narratwin-ai-frontend:ci .
