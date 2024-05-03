# crawler2/nurl.py
#
# internal representation of a node URL
#
# storing URLS as strings lacks the context necessary
# for filtering out bad URLs beyond its representation

from utils import get_urlhash, normalize
from urllib.parse import urlparse


# constants for nurl.status
NURL_STATUS_NO_DOWN = 0x0
NURL_STATUS_IN_USE = 0x1
NURL_STATUS_IS_DOWN = 0x2


# constants for nurl.finish
NURL_FINISH_OK = 0x0
NURL_FINISH_BAD = 0x1
NURL_FINISH_LOWINFO_PRE = 0x2
NURL_FINISH_LOWINFO_POST = 0x3
NURL_FINISH_TOO_EXACT = 0x4
NURL_FINISH_TOO_SIMILAR = 0x5
NURL_FINISH_NOT_ALLOWED = 0x6
NURL_FINISH_REDIRECT = 0x7
NURL_FINISH_SIFTED = 0x8
NURL_FINISH_CACHE_ERROR = 0xFF


def _compute_rel_dirdepth(child, parent):
    """Checks if the child URL is below the parent URL.
    Return the depth of the child relative from the parent (or -1 otherwise).
    Note: The query and fragments are discarded when computing the relative depth.

    Observe that depth in this context refers to the directory depth.
    As such, the function name appropriately includes "dirdepth".

    :param child str: The child URL (normalized)
    :param parent str: The parent URL (normalized)
    :return: The relative depth of the child from the parent
    :rtype: int
    """
    chld = urlparse(child)
    prnt = urlparse(parent)

    if chld.scheme != prnt.scheme or chld.netloc != prnt.netloc:
        # not in the same domain
        return -1

    if not chld.path.startswith(prnt.path):
        # not in the same hierarchy
        return -1

    # child URL must be below parent URL
    # return the difference in forward slash occurrences
    # if there is no difference, the URLs must be the same
    return chld.path.count('/') - prnt.path.count('/')


class Nurl:
    """Node URL encapsulation.
    Contains useful data about the URL not captured by URLs as a string.

    Depth is defined in the crawler graph context, NOT from the URL path string
    In other words, the length of the crawler path the URL was sourced from:
        -   `reldepth` of 2 indicates the URL was sourced from a path
            that followed a URL 1 level deep, twice.
        -   `absdepth` of 3 indicates the URL was sourced from a path
            that followed a URL, thrice.

    url         The URL itself.

    hash        The hash of the normalized URL.

    parent      The hash of the parent URL (where the URL was found).
                If the parent is unhashed as an absolute URL, then
                the URL does not exist as a nurl.

    status      The intermediate state of the URL as an int.
                    -   0x0: un-downloaded
                    -   0x1: in-use
                    -   0x2: downloaded

    finish      An internal marker that indicates the finish state of the URL
                after it was downloaded as an int.
                    -   0x0: ok
                    -   0x1: bad (i.e. no response)
                    -   0x2: low-info-pre
                    -   0x3: low-info-post
                    -   0x4: too-exact
                    -   0x5: too-similar
                    -   0x6: not-allowed
                    -   0x7: redirected
                    -   0xFF: cache server error (status=600+)

    absdepth    The absolute depth (relative to seed URL).

    reldepth    The depth relative to its parent URL.
                Depth increases by 1 if the URL is a level
                below the parent URL. Resets to 0 otherwise.

    monodepth   The monotonic depth relative to its parent URL.
                Depth increases by 1 if the URL is hierarchally
                below the parent URL. Resets to 0 otherwise.
                This is a looser version of `reldepth`.

    dupdepth    The depth of duplicate URLs.
                Depth increases by 1 if there's a match with
                the URL and the parent URL excluding queries and
                fragments. Resets to 0 otherwise.

    words       Tokenized word counts from the text content

    links       Links extracted from this URL (stored as hashes)

    exhash      Exact hash of the text content.

    smhash      Similarity hash for comparing against webpages.
                Also known as a fingerprint.

    """
    def __init__(self, url):
        """Initializes a Nurl object from the URL.

        :param url str: The URL
        """
        # internals
        self.url = url
        self.hash = get_urlhash(normalize(url))
        self.parent = None
        self.status = 0x0
        self.finish = 0x0

        # pre-processed
        self.absdepth = 0
        self.reldepth = 0
        self.monodepth = 0
        self.dupdepth = 0

        # post-processed
        self.words = dict()
        self.links = []
        self.exhash = None
        self.smhash = None


    @classmethod
    def from_dict(cls, dic):
        """Initializes a Nurl object from a dictionary.

        :param dic dict[str, Any]: A dictionary representing a Nurl
        """
        # allocate new Nurl instance
        nurl = cls.__new__(cls)

        # assign based on certain keys in dic
        # internals
        nurl.url = dic["url"]
        nurl.hash = get_urlhash(normalize(nurl.url))
        nurl.parent = dic["parent"]
        nurl.status = dic["status"]
        nurl.finish = dic["finish"]

        # pre-processed
        nurl.absdepth = dic["absdepth"]
        nurl.reldepth = dic["reldepth"]
        nurl.monodepth = dic["monodepth"]
        nurl.dupdepth = dic["dupdepth"]

        # post-processed
        nurl.words = dic["words"]
        nurl.links = dic["links"]
        nurl.exhash = dic["exhash"]
        nurl.smhash = dic["smhash"]

        return nurl


    def set_parent(self, parent):
        """Sets the parent of the nurl.
        Attributes are recomputed based on the parent.

        :param parent Nurl: The parent nurl.
        """
        # no parent
        # reset stats
        if parent == None:
            self.parent = None
            self.absdepth = 0
            self.reldepth = 0
            self.monodepth = 0
            self.dupdepth = 0
            return

        # normalize urls
        chld_url = normalize(self.url)
        prnt_url = normalize(parent.url)

        # sets parent to the parent URL hash
        parenthash = get_urlhash(prnt_url)
        self.parent = parenthash

        # computes the absolute depth
        # child is always 1 level deeper from parent relative to seed URL
        self.absdepth = parent.absdepth + 1

        # computes relative depth, monotonic depth, and duplicate depth
        # relative increases iff nurl is directly below parent
        # monotonic increases iff nurl is strictly below parent
        # duplicate increases iff nurl is in the same level as parent
        _rd, _md, _dd = 0, 0, 0
        _rel_dirdepth = _compute_rel_dirdepth(chld_url, prnt_url)
        if _rel_dirdepth == 0:
            # same level
            _rd, _md, _dd = (
                0,
                0,
                parent.dupdepth + 1
            )
        elif _rel_dirdepth >= 1:
            # below (directly and strictly)
            _rd, _md, _dd = (
                0 if _rel_dirdepth > 1 else parent.reldepth + 1,
                parent.monodepth + 1,
                0
            )
        self.reldepth = _rd
        self.monodepth = _md
        self.dupdepth = _dd

