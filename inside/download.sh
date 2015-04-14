#!/bin/bash

pushd /usr/src

while (($#)); do
    url=$1 ; shift
    tarball=$1 ; shift
    curl -Lfo "${tarball}" "${url}" || exit 1
done

popd
