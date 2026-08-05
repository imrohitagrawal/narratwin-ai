FROM node:26.6.0-alpine@sha256:a4fb14143ee24c038c851864fe85fd90f9121abc8fdca3092798bcc02e06b1d8 AS deps

ENV NEXT_TELEMETRY_DISABLED=1
ENV NPM_CONFIG_FUND=false
ENV NPM_CONFIG_UPDATE_NOTIFIER=false
ENV NPM_CONFIG_STRICT_ALLOW_SCRIPTS=true

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --strict-allow-scripts=true

FROM deps AS build

ARG NARRATWIN_API_PROXY_TARGET=http://127.0.0.1:8000
ENV NARRATWIN_API_PROXY_TARGET=${NARRATWIN_API_PROXY_TARGET}

COPY frontend ./
RUN npm run build

FROM cgr.dev/chainguard/node:latest@sha256:cf7ae5ead5aed79a61404d7b1bbb9b89ea461991b21cb8fcb07d4b6ad4d8b734 AS runner

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NARRATWIN_API_PROXY_TARGET=http://127.0.0.1:8000
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

WORKDIR /app

USER root
RUN ["/usr/bin/node", "-e", "const fs=require('fs'); for (const p of ['/usr/lib/node_modules/npm','/usr/bin/npm','/usr/bin/npx','/usr/local/lib/node_modules/npm','/usr/local/bin/npm','/usr/local/bin/npx']) fs.rmSync(p,{force:true,recursive:true})"]

COPY --from=build --chown=65532:65532 /app/.next/standalone ./
COPY --from=build --chown=65532:65532 /app/.next/static ./.next/static
USER 65532:65532

EXPOSE 3000
ENTRYPOINT ["/usr/bin/node"]
CMD ["server.js"]
