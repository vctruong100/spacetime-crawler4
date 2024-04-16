from urllib.parse import urlparse

# Track unique pages by the URL and discard the fragment parts

unqiue_pages = set()

def add_page(url):
    """
    Adds a page to the unique pages set
    :param url str: URL of the page
    :return: True if the page is unique, False otherwise
    :rtype: bool
    """
    parsed = urlparse(url)

    # remove fragments
    new_url = parsed._replace(fragment='').geturl()
    if new_url not in unqiue_pages:
        unqiue_pages.add(new_url)
        return True
    return False

