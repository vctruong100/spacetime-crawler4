# helpers/filter.py
#
# filters URLS by checking against certain thresholds
# uses the Nurl interface


# pre-selected threshold values for Nurl attributes
# feel free to change this
# see crawler2/nurl.py for more info on attributes
MAX_ABS_DEPTH = 16
MAX_REL_DEPTH = 3
MAX_MONO_DEPTH = 6
MAX_DUP_DEPTH = 1


def filter_pre(nurl):
    """Returns whether nurl should be filtered at the
    pre-processing stage (before the response is parsed).
    Note: nurl.set_parent() must be called prior to this function.

    :param nurl Nurl: The Nurl object
    :return: Whether Nurl passes the pre-filter
    :rtype: bool
    """
    return not (
        nurl.absdepth > MAX_ABS_DEPTH or
        nurl.reldepth > MAX_REL_DEPTH or
        nurl.monodepth > MAX_MONO_DEPTH or
        nurl.dupdepth > MAX_DUP_DEPTH
    )


def filter_post(nurl):
    """Returns whether nurl should be filtered at the
    post-processing stage (after response is parsed).
    Note: nurl.links and nurl.words must be set prior to this function

    :param nurl Nurl: The Nurl object
    :return: Whether Nurl passes the post-filter
    :rtype: bool
    """
    return True

