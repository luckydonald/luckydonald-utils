# -*- coding: utf-8 -*-
import re

__author__ = 'luckydonald'


REPO_NAME_REGEX = re.compile("([a-zA-Z0-9_.-]+)")

AT_USERNAME_REGEX = re.compile(  # https://regex101.com/r/eJ6cA4/
    "(?:\s|^|\.|,|:|\?|!|¡|¿)@(?!-)(?P<user>(?:[a-zA-Z0-9]|-(?!-))+[a-zA-Z0-9])(?![^\x00-\x7F])(?:$|[^a-zA-Z0-9\-_])"
)

SIMPLE_URL_REGEX = re.compile(
    r"(?:https?://(?:www\.)?|www\.|^|(?<=\s))github.com/[^\s]+")  # https://regex101.com/r/gH8xM9/4
""" :const:`SIMPLE_URL_REGEX`: A very simple url regex """

FILE_URL_REGEX = re.compile(  # https://regex101.com/r/qK6uN9/15
    "\\b(?P<url>(?P<protocol>https?://)?(?P<www>www\.)?github.com/(?P<user>[a-zA-Z0-9_-]+)/(?P<repo>[a-zA-Z0-9_.-]+)/?"
    "(?P<path>(?:(?P<kind>blob|tree)/(?P<branch>[a-zA-Z0-9_%-]+))/?(?P<file>[^\s#]*)/?)?)"
    "(?:#(?P<hash>[-;/?:@&=+$,_.!~*'()%0-9a-zA-Z]*))?(?:(?=\s)|$)", flags=re.IGNORECASE
)
"""
:const:`FILE_URL_REGEX`: Matching github urls with the following groups:
  - url: the complete url
      - protocol: "https://" or "http://" or empty/non-existent
      - user: git user or organisation
      - repo: the repository
      - path: When existent, this is not the project page (root of master)
          - kind: blob or tree
          - branch: the name of the branch (kind=tree), or the commit hash (kind=blob)
        - file: the rest of the filepath (from root of that branch, can be empty)
      - hash: Can be non-existent or empty. Everything behind the '#'
"""
