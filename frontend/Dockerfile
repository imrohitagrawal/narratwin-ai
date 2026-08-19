FROM node:26.7.0-bookworm-slim@sha256:cd565714d4da3e84bfd341e31448f81d47c6362198f152345297c9c1154e6341 AS node-source

FROM cgr.dev/chainguard/gcc-glibc@sha256:8cfe0b01dcf3ad08aa8d51811175749f7390228be059497ddc6d94551a68f66e AS atomic-source

USER root
RUN mkdir -p /runtime/usr/lib /runtime/var/lib/db/sbom \
    && cp -a /usr/lib/libatomic.so.1 /usr/lib/libatomic.so.1.2.0 /runtime/usr/lib/ \
    && cp /var/lib/db/sbom/libatomic-16.1.0-r4.spdx.json /runtime/var/lib/db/sbom/ \
    && awk 'BEGIN { keep=0 } /^P:libatomic$/ { keep=1 } keep { print } keep && /^$/ { exit }' \
       /usr/lib/apk/db/installed > /runtime/libatomic-record

FROM cgr.dev/chainguard/glibc-dynamic@sha256:eaec65b25f35619be16f4992e7bae1128eafcf63c114f2859b800a7020c1ef70 AS deps

ENV NEXT_TELEMETRY_DISABLED=1
ENV NPM_CONFIG_FUND=false
ENV NPM_CONFIG_UPDATE_NOTIFIER=false
ENV NPM_CONFIG_CACHE=/tmp/npm-cache

WORKDIR /app

USER root
COPY --from=node-source --chown=0:0 /usr/local/bin/node /usr/bin/node
COPY --from=node-source --chown=0:0 /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
COPY --from=atomic-source --chown=0:0 /runtime/ /
RUN ["/usr/bin/node", "-e", "const fs=require('fs'),p='/usr/lib/apk/db/installed',r=fs.readFileSync('/libatomic-record','utf8'); if(!/^P:libatomic$\\n^V:16\\.1\\.0-r4$/m.test(r)||/^P:libatomic$/m.test(fs.readFileSync(p,'utf8')))throw new Error('libatomic identity invalid'); fs.appendFileSync(p,r.endsWith('\\n\\n')?r:'\\n'+r+'\\n'); fs.rmSync('/libatomic-record')"]
RUN ["/usr/bin/node", "-e", "if(process.version!=='v26.7.0'||process.versions.openssl!=='3.5.7'||process.config.variables.node_shared_openssl!==false||process.config.variables.node_use_quic!==false)throw new Error('Node build identity or QUIC boundary invalid')"]

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

FROM deps AS build

ARG NARRATWIN_API_PROXY_TARGET=http://127.0.0.1:8000
ENV NARRATWIN_API_PROXY_TARGET=${NARRATWIN_API_PROXY_TARGET}

COPY frontend ./
RUN ["/usr/bin/node", "node_modules/next/dist/bin/next", "build"]

FROM cgr.dev/chainguard/glibc-dynamic@sha256:eaec65b25f35619be16f4992e7bae1128eafcf63c114f2859b800a7020c1ef70 AS runner

ENV NODE_VERSION=26.7.0
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NARRATWIN_API_PROXY_TARGET=http://127.0.0.1:8000
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app

USER root
COPY --from=node-source --chown=0:0 /usr/local/bin/node /usr/bin/node
COPY --from=atomic-source --chown=0:0 /runtime/ /
RUN ["/usr/bin/node", "-e", "const fs=require('fs'),p='/usr/lib/apk/db/installed',r=fs.readFileSync('/libatomic-record','utf8'); if(!/^P:libatomic$\\n^V:16\\.1\\.0-r4$/m.test(r)||/^P:libatomic$/m.test(fs.readFileSync(p,'utf8')))throw new Error('libatomic identity invalid'); fs.appendFileSync(p,r.endsWith('\\n\\n')?r:'\\n'+r+'\\n'); fs.rmSync('/libatomic-record'); for(const x of ['/usr/bin/ld.so','/usr/bin/ldconfig','/bin','/sbin','/usr/sbin'])fs.rmSync(x,{force:true,recursive:true})"]

COPY --from=build --chown=0:0 /app/.next/standalone ./
COPY --from=build --chown=0:0 /app/.next/static ./.next/static
RUN ["/usr/bin/node", "-e", "const fs=require('fs'); function secure(p){const s=fs.lstatSync(p); if(s.isSymbolicLink()){fs.lchownSync(p,0,0);return} fs.chownSync(p,0,0); fs.chmodSync(p,s.isDirectory()?0o755:(s.mode&0o111)?0o755:0o644); if(s.isDirectory())for(const n of fs.readdirSync(p))secure(p+'/'+n)} secure('/app')"]
USER 65532:65532

EXPOSE 3000
ENTRYPOINT ["/usr/bin/node"]
CMD ["server.js"]
