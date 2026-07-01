FROM node:26-alpine@sha256:725aeba2364a9b16beae49e180d83bd597dbd0b15c47f1f28875c290bfd255b9 AS deps

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

FROM node:26-alpine@sha256:725aeba2364a9b16beae49e180d83bd597dbd0b15c47f1f28875c290bfd255b9 AS runner

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NARRATWIN_API_PROXY_TARGET=http://127.0.0.1:8000
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

WORKDIR /app

RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx

COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
USER node

EXPOSE 3000
CMD ["node", "server.js"]
