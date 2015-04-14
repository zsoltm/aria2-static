#!/usr/bin/env python2

import os
import logging.config
script_root = os.path.dirname(os.path.realpath(__file__))
if __name__ == '__main__':
    os.chdir(script_root)
    logging.config.fileConfig('inside/logging.conf')

import sys
import platform
from subprocess import CalledProcessError, check_call
from work_dir import work_dir
from git_api import get_release_tags_by_name, get_releases_by_tag_name


__log = logging.getLogger(__name__)
build_architectures = {
    "armv7l": "zsoltm/buildpack-deps:jessie-armhf",
    "x86_64": "buildpack-deps:jessie"
}
architectures = build_architectures.keys()
host_arch = platform.machine() or "x86_64"
min_version = "1.18.10"
tag_version = lambda tag_name: tag_name[8:]
version_tag = lambda version: "release-%s" % version
artifact_name = lambda version, arch: "aria2-%s-static-%s.tar.xz" % (version, arch)
src_tarball_name = lambda version: "aria2-src-%s.tar.gz" % version


def get_tokens():
    from netrc import netrc

    nrc = netrc()
    auth = nrc.authenticators("github.com")
    api_auth = nrc.authenticators("api.github.com")
    uploads_auth = nrc.authenticators("uploads.github.com")

    if api_auth is None or uploads_auth is None:
        print("No tokens fund in .netrc, please set github.com; api.github.com and uploads.github.com tokens")
        sys.exit(1)

    return auth[0], api_auth[0], uploads_auth[0]


def get_upstream_release_tags():
    return get_release_tags_by_name("tatsuhiro-t", "aria2", min_version, tag_version)


def get_my_releases():
    return get_releases_by_tag_name("zsoltm", "aria2-static")


def get_missing_release_tag_names(releases, tags):
    return tags.viewkeys() - releases.viewkeys()


def get_missing_artifacts(tags, my_releases):
    missing_release_tags = get_missing_release_tag_names(my_releases, tags)
    missing_arch_by_tag = {}

    for tag_name, release_data in my_releases.iteritems():
        assets = set((str(asset[u"name"]) for asset in release_data[u"assets"]))
        for arch in architectures:
            tarball = artifact_name(tag_version(str(tag_name)), arch)
            if tarball not in assets:
                missing_arch_by_tag[tag_name] = missing_arch_by_tag.get(tag_name, []) + [arch]

    for missing_tag in missing_release_tags:
        for arch in architectures:
            missing_arch_by_tag[missing_tag] = missing_arch_by_tag.get(missing_tag, []) + [arch]

    return missing_arch_by_tag


def execute(cmd, **kwargs):
    __log.debug("executing: %s", " ".join(cmd))
    check_call(cmd, **kwargs)


def download_all_sources(missing_architectures_by_version, upstream_release_tags):
    def append_tuple(prev, tarball):
        return prev + list(tarball)

    tarballs = [(upstream_release_tags[version][u"tarball_url"], src_tarball_name(tag_version(version)))
                for version in missing_architectures_by_version.viewkeys()]
    cmd = reduce(append_tuple, tarballs, [
        "docker", "run", "-it", "--rm",
        "-v", "%s:/build" % os.path.join(script_root, "inside"),
        "-v", "%s:/usr/src" % os.getcwd(),
        build_architectures[host_arch], "bash", "/build/download.sh"])

    __log.info("launching %s docker container for downloading sources", host_arch)
    execute(cmd)


def build(arch, versions, wd_out):
    try:
        __log.debug("launching docker container for %s", arch)
        cmd = ["docker", "run", "-it", "--rm",
               "-v", "%s:/build" % os.path.join(script_root, "inside"),
               "-v", "%s:/out" % wd_out,
               "-v", "%s:/usr/src" % os.getcwd(),
               build_architectures[arch], "bash", "/build/build.sh"] + [arch] + versions
        execute(cmd)
    except CalledProcessError:
        __log.error("unsuccessful embedded build execution, aborting")
        sys.exit(2)


def tag_and_upload(wd_out, missing_architectures_by_version, my_releases):
    def artifact_reduce(prev, current):
        tag_name, arch_list = current
        for arch in arch_list:
            version = tag_version(tag_name)
            prev += [version, tag_name, arch, artifact_name(version, arch)]
        return prev

    _release_tags = get_release_tags_by_name("zsoltm", "aria2-static")

    artifacts = reduce(artifact_reduce, missing_architectures_by_version.iteritems(), [])
    missing_tags = reduce(lambda prev, current: prev + [current],
                          missing_architectures_by_version.viewkeys() - _release_tags.viewkeys(), [])
    missing_releases = reduce(lambda prev, current: prev + [current, tag_version(current)],
                              missing_architectures_by_version.viewkeys() - my_releases.viewkeys(), [])

    token, api_token, uploads_token = get_tokens()

    cmd = ["docker", "run", "-it", "--rm",
           "-v", "%s:/build" % os.path.join(script_root, "inside"),
           "-v", "%s:/out" % wd_out,
           "-e", "TOKEN=%s" % token,
           "-e", "API_TOKEN=%s" % api_token,
           "-e", "UPLOADS_TOKEN=%s" % uploads_token,
           build_architectures[host_arch],
           "bash", "/build/tag_and_upload.sh"] \
        + missing_tags + ["--"] + missing_releases + ["--"] + artifacts

    execute(cmd)


def build_all_arch(missing_architectures_by_version, my_releases):
    def missing_versions(architecture):
        return [tag_version(release) for release, arch_list in missing_architectures_by_version.iteritems()
                if architecture in arch_list]

    with work_dir(cwd=False) as wd_out:
        __log.debug(missing_architectures_by_version)
        for arch in architectures:
            versions = missing_versions(arch)
            if versions:
                __log.info("building: %s on %s" % ("; ".join(versions), arch))
                build(arch, versions, wd_out)

        tag_and_upload(wd_out, missing_architectures_by_version, my_releases)


def main():
    upstream_release_tags = get_upstream_release_tags()
    my_releases = get_my_releases()
    missing_architectures_by_version = get_missing_artifacts(upstream_release_tags, my_releases)

    if missing_architectures_by_version:
        with work_dir():
            download_all_sources(missing_architectures_by_version, upstream_release_tags)
            build_all_arch(missing_architectures_by_version, my_releases)


if __name__ == "__main__":
    main()
