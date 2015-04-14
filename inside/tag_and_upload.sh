#!/bin/bash

if [ "$#" -lt 2 ]; then
    echo "Usage tag_and_upload.sh tag1 tag2 -- tag3 release3 tag4 release4 -- release1 tag1 arch1 artifact1 ..."
    exit 1
fi

git config --global push.default simple\
 && git config --global user.email "zsolt@jessie.vm"\
 && git config --global user.name "Zsolt M" || exit 2

printf "machine github.com\n\
  login ${TOKEN}\n\n\
machine api.github.com\n\
  login ${API_TOKEN}\n\n\
machine uploads.github.com\n\
  login ${UPLOADS_TOKEN}\n" >> ~/.netrc

tmpDir=`mktemp -d`

pushd /usr/src
git clone --depth 1 https://github.com/zsoltm/aria2-static.git || exit 3
pushd aria2-static
while [ "$1" != "--" ]; do
    tagName=$1 ; shift
    echo "git tag ${tagName}"
    git tag "${tagName}"\
     && git push origin "${tagName}"
done
popd
shift

while [ "$1" != "--" ]; do
    tagName=$1 ; shift
    release=$1 ; shift
    echo "create release ${release} for tag ${tagName}"

    curl -nfLX POST https://api.github.com/repos/zsoltm/aria2-static/releases\
     -H "Content-Type: application/json; encoding=UTF-8"\
     --data "{\"tag_name\":\"${tagName}\",\"name\":\"${release}\"}" > "${tmpDir}/release-${release}.json"\
     || exit 4
done
shift

while (($#)); do
    release=$1 ; shift
    tagName=$1 ; shift
    arch=$1 ; shift
    artifact=$1 ; shift
    echo "adding artifact ${artifact} to release ${release} (tag: ${tagName})"

    if [ ! -f "${tmpDir}/release-${release}.json" ]; then
        echo "missing ${tmpDir}/release-${release}.json attempting to download"
        curl -nfL "https://api.github.com/repos/zsoltm/aria2-static/releases/tags/${tagName}"\
         > "${tmpDir}/release-${release}.json"\
         || exit 5
    fi

    uploadUrl=$(grep '"upload_url": "' "${tmpDir}/release-${release}.json" | grep -o 'https://[^"{]*')

    curl -nfLX POST "${uploadUrl}?name=aria2-${release}-static-${arch}.tar.xz"\
     -H "Content-Type: application/octet-stream"\
     --data-binary @/out/aria2-${release}-static-${arch}.tar.xz\
     || exit 6

done

rm -Rf ${tmpDir}

popd
