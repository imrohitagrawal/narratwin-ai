FROM node:26.7.0-alpine3.24@sha256:aadf416b2cdce311a8811ba3f0608a61b77dbf997500e2eafe781b51f6a0b019 AS node-source

USER root
RUN ["/usr/local/bin/node", "-e", "if(process.version!=='v26.7.0'||process.versions.openssl!=='3.5.7'||process.config.variables.node_shared_openssl!==false||process.config.variables.node_use_quic!==false)throw new Error('Node build identity or QUIC boundary invalid')"]
RUN set -eux; \
    apk add --root /runtime --initdb --no-cache --no-scripts \
      --keys-dir /etc/apk/keys \
      --repositories-file /etc/apk/repositories \
      alpine-keys=2.6-r0 \
      alpine-release=3.24.1-r0 \
      ca-certificates-bundle=20260611-r0 \
      libgcc=15.2.0-r5 \
      libstdc++=15.2.0-r5 \
      musl=1.2.6-r2; \
    mkdir -p /runtime/usr/bin /runtime/app /runtime/tmp; \
    cp /usr/local/bin/node /runtime/usr/bin/node; \
    chmod 0755 /runtime/usr/bin/node; \
    chmod 1777 /runtime/tmp; \
    test -s /runtime/lib/apk/db/installed; \
    test ! -e /runtime/bin/sh

FROM scratch AS deps

ENV NEXT_TELEMETRY_DISABLED=1
ENV NPM_CONFIG_FUND=false
ENV NPM_CONFIG_UPDATE_NOTIFIER=false
ENV NPM_CONFIG_CACHE=/tmp/npm-cache

WORKDIR /app

COPY --from=node-source /runtime/ /
COPY --from=node-source /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm

ADD --checksum=sha256:5dbb86c71d07a1957f2e90734092dd6a58bdcd9ebc2d8d41ca1c6e6a21d364e1 https://registry.npmjs.org/npm/-/npm-12.0.2.tgz /tmp/frontend-npm-archives/npm-12.0.2.tgz
ADD --checksum=sha256:5d06001fddd25cbee90c96db4dc5b7b57711b984c3141e28d10f143deb52dbaf https://registry.npmjs.org/brace-expansion/-/brace-expansion-5.0.9.tgz /tmp/frontend-npm-archives/brace-expansion-5.0.9.tgz
ADD --checksum=sha256:ad1790063beea11a312c801df30d58e147de762f4f77787552376eb7424623e5 https://registry.npmjs.org/ip-address/-/ip-address-10.3.1.tgz /tmp/frontend-npm-archives/ip-address-10.3.1.tgz
ADD --checksum=sha256:bcedf25a21daecd1a18fb5e19ab855b7d79ec8ef1da175e8ba85cfc0ed0069d1 https://registry.npmjs.org/tar/-/tar-7.5.21.tgz /tmp/frontend-npm-archives/tar-7.5.21.tgz
ADD --checksum=sha256:32a86c6fa28fd48b915555048c05bbd37ad35457d9e945953831a4374c886a9c https://registry.npmjs.org/undici/-/undici-6.28.0.tgz /tmp/frontend-npm-archives/undici-6.28.0.tgz
COPY scripts/ci/prepare_frontend_npm.mjs /tmp/prepare_frontend_npm.mjs
RUN ["/usr/bin/node", "/tmp/prepare_frontend_npm.mjs"]

COPY frontend/package.json frontend/package-lock.json ./
RUN ["/usr/bin/node", "/usr/local/lib/node_modules/npm/bin/npm-cli.js", "ci", "--ignore-scripts"]
RUN ["/usr/bin/node", "-e", "require('fs').rmSync('/tmp/npm-cache',{recursive:true,force:true})"]

FROM scratch AS build

ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/sbin:/bin
ENV NODE_VERSION=26.7.0
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NARRATWIN_API_PROXY_TARGET=http://127.0.0.1:8000
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

LABEL org.opencontainers.image.source="https://github.com/imrohitagrawal/narratwin-ai"
LABEL org.opencontainers.image.title="NarraTwin AI frontend runtime"
LABEL org.opencontainers.image.vendor="NarraTwin AI"

WORKDIR /app

COPY --from=node-source /runtime/ /

RUN --mount=from=deps,source=/app,target=/mnt/deps,readonly \
    --mount=type=bind,source=frontend,target=/mnt/frontend,readonly \
    --mount=type=bind,source=scripts/ci/prepare_frontend_npm.mjs,target=/tmp/prepare_frontend_npm.mjs,readonly \
    ["/usr/bin/node", "--input-type=module", "-e", "const fs=await import('node:fs'),m=await import('/tmp/prepare_frontend_npm.mjs');await m.assembleFrontendRuntime();const a=process.arch==='arm64'?'arm64':'x64',p=`node_modules/@img/sharp-libvips-linuxmusl-${a}/lib/libvips-cpp.so.8.18.3`;fs.copyFileSync(`/mnt/deps/${p}`,`/app/${p}`)"]

USER 65532:65532
EXPOSE 3000
ENTRYPOINT ["/usr/bin/node"]
CMD ["server.js"]
