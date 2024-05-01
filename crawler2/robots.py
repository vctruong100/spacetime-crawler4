# crawler2/robots.py
#
# Downloads robots.txt
# Returns the robot file parser for that file

from crawler2.download import download
from urllib.robotparser import RobotFileParser


def robots(netloc, config=None, logger=None, use_cache=False):
    """Downloads robots.txt from the netloc and reads it.
    If `use_cache` is True, then it downloads from the cache server instead.

    Returns a RobotFileParser for the specific domain.

    :param netloc str: The net location
    :param use_cache bool: Whether robots.txt should source from cache server
    :return: The RobotFileParser for the netloc
    :rtype: RobotFileParser

    """
    robots_url = f"{netloc}/robots.txt"
    robots_parser = RobotFileParser()

    resp = download(
        robots_url,
        config=config,
        logger=logger,
        use_cache=use_cache
    )

    logger.info(
        f"Downloaded robots {robots_url} "
        f"(status={resp.status}) "
        f"(error='{resp.error}')"
    )

    # assume allow-all is True if the cache server fails
    if resp.raw_response == None:
        robots_parser.allow_all = True
        return robots_parser

    # from urllib/robotparser.py
    # disallow if forbidden (403) or unauthorized (401)
    if resp.status in (401, 403):
        robots_parser.disallow_all = True
        return robots_parser

    # from urllib/robotparser.py
    # allow if robots.txt not found
    if resp.status >= 400 and resp.status < 500:
        robots_parser.allow_all = True
        return robots_parser

    # parse raw content if successful (200)
    if resp.status == 200:
        lines = resp.raw_response.content.decode("utf-8").splitlines()
        robots_parser.parse(lines)

    return robots_parser

