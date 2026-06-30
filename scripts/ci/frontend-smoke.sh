#!/usr/bin/env bash
set -euo pipefail

cd frontend
if [ ! -d node_modules ]; then
  npm ci --strict-allow-scripts=true
fi
npm run build
if [ "${CI:-}" = "true" ]; then
  npx playwright install --with-deps chromium
elif [ "${PLAYWRIGHT_SKIP_INSTALL:-}" = "1" ]; then
  echo "Skipping local Playwright browser install because PLAYWRIGHT_SKIP_INSTALL=1."
else
  npx playwright install chromium
fi

unset FORCE_COLOR
unset NO_COLOR
npm run test:smoke
