import logging
import urllib2
import json
from distutils.version import StrictVersion

logger = logging.getLogger(__name__)


def cmp_versions2(version1, version2=None):
    strict_version1 = StrictVersion(version1)
    return cmp(strict_version1, StrictVersion(version2)) if version2 is not None \
        else lambda version: cmp(strict_version1, StrictVersion(version))


def filter_release_tags(tags):
    return (tag for tag in tags if tag[u"name"].startswith("release-"))


def filter_release_tags_gt(tags, version, fn=lambda x: x):
    comparator = cmp_versions2(version)
    return (tag for tag in tags if comparator(fn(tag[u"name"])) <= 0)


def transpose_by(items, fn):
    def put(prev, current):
        prev[fn(current)] = current
        return prev

    return reduce(put, items, {})


def transpose_by_name(items):
    return transpose_by(items, lambda item: item[u"name"])


def transpose_by_tag_name(items):
    return transpose_by(items, lambda item: item[u"tag_name"])


def github_api_get(path):
    url = "https://api.github.com%s" % path
    logger.debug("api call %s", url)
    response = urllib2.urlopen(url)
    try:
        return json.loads(response.read())
    finally:
        response.close()


def get_tags(user, repo):
    return github_api_get("/repos/%s/%s/tags" % (user, repo))


def get_releases(user, repo):
    return github_api_get("/repos/%s/%s/releases" % (user, repo))


def get_releases_by_tag_name(user, repo):
    return transpose_by_tag_name(get_releases(user, repo))


def get_release_tags_by_name(user, repo, min_version=None, fn=lambda x: x):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("fetching release tags for %s/%s %s" % (
            user, repo,
            "(no minimum version limit)" if min_version is None else "with minimum version %s" % min_version))
    tags = get_tags(user, repo)
    release_tags = filter_release_tags(tags)
    return transpose_by_name(
        release_tags if min_version is None
        else filter_release_tags_gt(release_tags, min_version, fn))
