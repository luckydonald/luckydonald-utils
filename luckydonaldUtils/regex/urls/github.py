# -*- coding: utf-8 -*-
import re

__author__ = 'luckydonald'

from ..github import _USER_NAME_REGEX, _REPO_NAME_REGEX

# https://regex101.com/r/gH8xM9/4
_SIMPLE_URL_REGEX = r"(?:https?://(?:www\.)?|www\.|^|(?<=\s))github.com/[^\s]+"
SIMPLE_URL_REGEX = re.compile(_SIMPLE_URL_REGEX)
""" :const:`SIMPLE_URL_REGEX`: A very simple url regex """

# https://regex101.com/r/qK6uN9/15
_FILE_URL_REGEX = (
        r"\b(?P<url>(?P<protocol>https?://)?(?P<www>www\.)?github.com/"
        r"(?P<user>" + _USER_NAME_REGEX + ")/"
                                          r"(?P<repo>" + _REPO_NAME_REGEX + ")/?"
                                                                            r"(?P<path>(?:(?P<kind>blob|tree)/(?P<branch>[a-zA-Z0-9_%-]+))/?(?P<file>[^\s#]*)/?)?)"
                                                                            r"(?:#(?P<hash>[-;/?:@&=+$,_.!~*'()%0-9a-zA-Z]*))?(?:(?=\s)|$)"
)
FILE_URL_REGEX = re.compile(  # https://regex101.com/r/qK6uN9/15
    _FILE_URL_REGEX, flags=re.IGNORECASE
)
"""
:const:`FILE_URL_REGEX`: Matching github urls with the following named matching groups:

- `url`: the complete url

    - `protocol`: "https://" or "http://" or empty/non-existent
    - `user`: git user or organisation
    - `repo`: the repository
    - `path`: When existent, this is not the project page (root of master)

        - `kind`: blob or tree
        - `branch`: the name of the branch (kind=tree), or the commit hash (kind=blob)
        - `file`: the rest of the filepath (from root of that branch, can be empty)

    - `hash`: Can be non-existent or empty. Everything behind the '#'
"""
