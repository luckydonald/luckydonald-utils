# -*- coding: utf-8 -*-
import re

__author__ = 'luckydonald'


REPO_NAME_REGEX = re.compile("([a-zA-Z0-9_.-]+)")

GITHUB_FILE_REGEX = re.compile(  # https://regex101.com/r/qK6uN9/7
    "\\b(?P<url>https?://github.com/(?P<user>[a-zA-Z0-9_-]+)/(?P<repo>[a-zA-Z0-9_.-]+)/?"
    "(?P<path>(?:(?P<kind>blob|tree)/(?P<branch>[a-zA-Z0-9_%-]+/?)/?)(?P<file>[^\s]*)/?)?)(?:\\s|$)"
)
"""
Matching groups:
  - url: the complete url
      - user: git user or organisation
      - repo: the repository
      - path: When existent, this is not the project page (root of master)
          - kind: blob or tree
          - branch: the name of the branch (kind=tree), or the commit hash (kind=blob)
        - file: the rest of the filepath (from root of that branch, can be empty)
"""