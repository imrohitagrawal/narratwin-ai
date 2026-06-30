#!/usr/bin/env bash
set -euo pipefail

docker build -f backend/Dockerfile -t narratwin-ai-backend:ci .
docker build -f frontend/Dockerfile -t narratwin-ai-frontend:ci .
