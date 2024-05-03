# crawler2/download.py
#
# downloads file either using requests.get
# or using the cache server

import utils.response
import utils.download
import requests

def _fake_response(resp):
    """Creates a blanket Response object that uses
    the interface defined in utils.response.Response.
    """
    resp2 = utils.response.Response.__new__(utils.response.Response)
    resp2.url = resp.url
    resp2.status = resp.status_code
    resp2.raw_response = resp
    resp2.error = ""
    return resp2


def download(url, config=None, logger=None, use_cache=False):
    """Fetches the response of the URL
    either from requests.get(...) or the cache server.
    The source is switched via `use_cache`.

    The returned response object shall use the interface defined in
    utils.response.Response.

    :param url str: The URL string
    :return: A result tuple
    :rtype: Response

    """
    if not use_cache:
        resp = requests.get(url)
        return _fake_response(resp)
    else:
        resp = utils.download.download(url, config, logger)
        return resp

