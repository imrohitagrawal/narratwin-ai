#!/usr/bin/env bash
set -euo pipefail

cd frontend
npm ci --strict-allow-scripts=true
npm run lint
npm run typecheck
npm test
npm run build
