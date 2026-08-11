FROM node:26.6.0-alpine@sha256:a4fb14143ee24c038c851864fe85fd90f9121abc8fdca3092798bcc02e06b1d8 AS deps

ENV NEXT_TELEMETRY_DISABLED=1
ENV NPM_CONFIG_FUND=false
ENV NPM_CONFIG_UPDATE_NOTIFIER=false
ENV NPM_CONFIG_STRICT_ALLOW_SCRIPTS=true

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm pack npm@12.0.2 brace-expansion@5.0.9 ip-address@10.3.1 tar@7.5.21 undici@6.28.0 \
      --pack-destination /tmp --silent \
    && echo 'b885e890b9418fa1693544d05f53e64f9a73ec194837d4258b15fecdd692347b1dd2a517b1b0cbaf9d31cd8e92c3b70956bd2ecc72833a57b4b3098f5bfa7943  /tmp/npm-12.0.2.tgz' | sha512sum -c - \
    && echo '49c43822ebc8105d533253fb66dfaf8c9ffff7394f6f64837315b13376e4f2ceade8619d27b28ed5d09c4e274e3c929e3d6df42c4ff6713ef00b23e1a3dfd6c6  /tmp/brace-expansion-5.0.9.tgz' | sha512sum -c - \
    && echo 'd5ef5dde46fdecd1c94c8243656f6b2aa5b687af9d15ae740f2d1fa4f48c429d800e37b982f2ac5e67622ba770639b7be93693b79f8fe4dd58fcba13a08c4fea  /tmp/ip-address-10.3.1.tgz' | sha512sum -c - \
    && echo '5dd86d0af94ccb0c31a425bc604ab794e5c126950f4d1d8e1c77302cf3b71f0b09a8e1dad8e93fa09eebb86ce9f89acaa113d50b327001d123a8b5bfbcd44f1c  /tmp/tar-7.5.21.tgz' | sha512sum -c - \
    && echo '2c863dd7483d4c8d77612f7996b305aecf119bfbbf8ab8077935a8282a2d79e274e02509f767847e3d2b567fbb54a30f06950f894a0129f84dc8b236dc413f28  /tmp/undici-6.28.0.tgz' | sha512sum -c - \
    && rm -rf /usr/local/lib/node_modules/npm \
    && mkdir -p /usr/local/lib/node_modules/npm \
    && tar -xzf /tmp/npm-12.0.2.tgz -C /usr/local/lib/node_modules/npm --strip-components=1 \
    && for package in brace-expansion ip-address tar undici; do \
         rm -rf "/usr/local/lib/node_modules/npm/node_modules/${package}"; \
         mkdir -p "/usr/local/lib/node_modules/npm/node_modules/${package}"; \
       done \
    && tar -xzf /tmp/brace-expansion-5.0.9.tgz -C /usr/local/lib/node_modules/npm/node_modules/brace-expansion --strip-components=1 \
    && tar -xzf /tmp/ip-address-10.3.1.tgz -C /usr/local/lib/node_modules/npm/node_modules/ip-address --strip-components=1 \
    && tar -xzf /tmp/tar-7.5.21.tgz -C /usr/local/lib/node_modules/npm/node_modules/tar --strip-components=1 \
    && tar -xzf /tmp/undici-6.28.0.tgz -C /usr/local/lib/node_modules/npm/node_modules/undici --strip-components=1
RUN npm ci --strict-allow-scripts=true && rm -rf /root/.npm /tmp/*.tgz

FROM deps AS build

ARG NARRATWIN_API_PROXY_TARGET=http://127.0.0.1:8000
ENV NARRATWIN_API_PROXY_TARGET=${NARRATWIN_API_PROXY_TARGET}

COPY frontend ./
RUN npm run build

FROM node:26.7.0-bookworm-slim@sha256:cd565714d4da3e84bfd341e31448f81d47c6362198f152345297c9c1154e6341 AS node-source

FROM cgr.dev/chainguard/gcc-glibc@sha256:8cfe0b01dcf3ad08aa8d51811175749f7390228be059497ddc6d94551a68f66e AS atomic-source

USER root
RUN mkdir -p /runtime/usr/lib /runtime/var/lib/db/sbom \
    && cp -a /usr/lib/libatomic.so.1 /usr/lib/libatomic.so.1.2.0 /runtime/usr/lib/ \
    && cp /var/lib/db/sbom/libatomic-16.1.0-r4.spdx.json /runtime/var/lib/db/sbom/ \
    && awk 'BEGIN { keep=0 } /^P:libatomic$/ { keep=1 } keep { print } keep && /^$/ { exit }' \
       /usr/lib/apk/db/installed > /runtime/libatomic-record

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
