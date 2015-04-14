#!/bin/bash

if [ "$#" -lt 2 ]; then
    echo "Illegal number of parameters, architecture and one or more versions should be passed" && exit 1
fi

arch=$1
shift

apt-get update && apt-get install -y autopoint libgcrypt-dev libcppunit-dev || exit 2


while (($#)); do
    buildDir=$(mktemp -d)
    version=$1
    shift

    pushd ${buildDir}

    mkdir src-${version}
    tar xvf /usr/src/aria2-src-${version}.tar.gz --strip-components 1 -C src-${version}
    mkdir -p usr/local

    pushd src-${version}
    autoreconf -i\
     && ./configure\
        --prefix "${buildDir}/usr/local"\
        --with-openssl\
        --without-gnutls\
        --with-libexpat\
        --without-libxml2\
        ARIA2_STATIC=yes\
     && make -j4\
     && make install\
     || exit 3

    popd

    strip -s usr/local/bin/aria2c
#    mkdir -p usr/local/bin && touch usr/local/bin/test.sh
    tar cJvf /out/aria2-${version}-static-${arch}.tar.xz usr/
    popd
done
