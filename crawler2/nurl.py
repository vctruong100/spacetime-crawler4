# crawler2/nurl.py
#
# internal representation of a node URL
#
# storing URLS as strings lacks the context necessary
# for filtering out bad URLs beyond its representation


class Nurl:
    """Node URL encapsulation.
    Contains useful data about the URL not captured by URLs as a string.

    url         The URL itself.
    status      Whether the URL was downloaded.
    parent      The hash of the parent URL (where the URL was found).

    absdepth    The absolute depth (relative to seed URL).

    reldepth    The depth relative to its parent URL
                Depth increases by 1 if the URL is a level
                below the parent URL. Resets to 0 otherwise.
    """
    def __init__(self, url, d=None):
        if d:
            self.url = d["url"]
            self.status = d["status"]
            self.parent = d["parent"]
            self.absdepth = d["absdepth"]
            self.reldepth = d["reldepth"]
        else:
            self.url = url
            self.status = False
            self.parent = None
            self.absdepth = 0
            self.reldepth = 0

