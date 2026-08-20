FROM docker.io/library/alpine:3.21@sha256:48b0309ca019d89d40f670aa1bc06e426dc0931948452e8491e3d65087abc07d AS cpython-build

ENV PATH=/usr/local/bin:$PATH
ENV PYTHON_VERSION=3.13.15
ENV PYTHON_SHA256=1e66a7945a48390ee4c2a4268a0e4185884059a13c4aab6d148aa208deea4a76
RUN set -eux; \
    apk add --no-cache \
      bluez-dev build-base bzip2-dev expat-dev gdbm-dev gnupg \
      libffi-dev libnsl-dev libtirpc-dev linux-headers ncurses-dev \
      openssl-dev=3.3.7-r0 pax-utils readline-dev sqlite-dev tar \
      tcl-dev tk-dev util-linux-dev wget xz-dev zlib-dev; \
    wget -O python.tar.xz \
      "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz"; \
    echo "$PYTHON_SHA256 *python.tar.xz" | sha256sum -c -; \
    wget -O python.tar.xz.asc \
      "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz.asc"; \
    export GNUPGHOME="$(mktemp -d)"; \
    python_gpg_fingerprint=7169605F62C751356D054A26A821E680E5FA6305; \
    gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$python_gpg_fingerprint"; \
    gpg --batch --verify python.tar.xz.asc python.tar.xz; \
    gpgconf --kill all; \
    rm -rf "$GNUPGHOME" python.tar.xz.asc; \
    mkdir -p /usr/src/python; \
    tar --extract --directory /usr/src/python --strip-components=1 --file python.tar.xz; \
    rm python.tar.xz; \
    cd /usr/src/python; \
    gnuArch="$(gcc -dumpmachine)"; \
    ./configure \
      --build="$gnuArch" \
      --enable-loadable-sqlite-extensions \
      --enable-option-checking=fatal \
      --enable-shared \
      --with-ensurepip; \
    EXTRA_CFLAGS="-DTHREAD_STACK_SIZE=0x100000 -fno-omit-frame-pointer -mno-omit-leaf-frame-pointer"; \
    LDFLAGS="-Wl,--strip-all"; \
    make -j "$(nproc)" EXTRA_CFLAGS="$EXTRA_CFLAGS" LDFLAGS="$LDFLAGS"; \
    rm python; \
    make -j "$(nproc)" EXTRA_CFLAGS="$EXTRA_CFLAGS" \
      LDFLAGS="$LDFLAGS -Wl,-rpath='\$\$ORIGIN/../lib'" python; \
    make install; \
    cd /; \
    rm -rf /usr/src/python; \
    find /usr/local -depth \
      \( \( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
      -o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \) \
      -exec rm -rf '{}' +; \
    ln -s python3 /usr/local/bin/python; \
    ln -s pip3 /usr/local/bin/pip

RUN set -eux; \
    rm -f /usr/local/lib/python3.13/lib-dynload/_sqlite3*.so; \
    runtime_deps="$(find /usr/local -type f -executable -not -name '*tkinter*' \
      -exec scanelf --needed --nobanner --format '%n#p' '{}' ';' \
      | tr ',' '\n' | sort -u \
      | awk 'system("[ -e /usr/local/lib/" $1 " ]") == 0 { next } { print "so:" $1 }')"; \
    apk add --root /runtime --initdb --no-cache --no-scripts \
      --keys-dir /etc/apk/keys --repositories-file /etc/apk/repositories \
      alpine-keys=2.5-r0 alpine-release=3.21.7-r0 ca-certificates-bundle tzdata \
      libcrypto3=3.3.7-r0 libssl3=3.3.7-r0 $runtime_deps; \
    mkdir -p /runtime/usr /runtime/etc /runtime/app /runtime/tmp; \
    cp -a /usr/local /runtime/usr/; \
    rm -rf /runtime/usr/local/lib/python3.13/site-packages/pip \
      /runtime/usr/local/lib/python3.13/site-packages/pip-*.dist-info; \
    rm -f /runtime/usr/local/bin/pip /runtime/usr/local/bin/pip3*; \
    printf 'appuser:x:10001:10001:appuser:/app:/sbin/nologin\n' > /runtime/etc/passwd; \
    printf 'appuser:x:10001:\n' > /runtime/etc/group; \
    chmod 1777 /runtime/tmp; \
    test -s /runtime/lib/apk/db/installed; \
    grep -q '^P:libcrypto3$' /runtime/lib/apk/db/installed; \
    grep -q '^P:libssl3$' /runtime/lib/apk/db/installed; \
    /runtime/usr/local/bin/python3 --version

FROM cpython-build AS backend-build

ENV PATH=/usr/local/bin:$PATH \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
RUN python -m pip install --no-cache-dir uv==0.11.32
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend ./backend

FROM scratch

COPY --from=cpython-build /runtime/ /
COPY --from=backend-build --chown=10001:10001 /app /app

ENV PATH=/app/.venv/bin:/usr/local/bin \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=container

WORKDIR /app
USER 10001:10001
EXPOSE 8000
CMD [".venv/bin/uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
