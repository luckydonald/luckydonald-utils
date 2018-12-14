# -*- coding: utf-8 -*-
import re

__author__ = 'luckydonald'

_REPO_NAME_REGEX = r"[a-zA-Z0-9_.-]+"
REPO_NAME_REGEX = re.compile(_REPO_NAME_REGEX)

_USER_NAME_REGEX = r"(?:[a-zA-Z0-9]|-(?!-))+[a-zA-Z0-9]"
USER_NAME_REGEX = re.compile(_USER_NAME_REGEX)

# https://regex101.com/r/eJ6cA4/
_AT_USERNAME_REGEX = (
        r"(?:\s|^|\.|,|:|\?|!|¡|¿)@(?!-)"
        r"(?P<user>" + _USER_NAME_REGEX + r")"
                                          r"(?![^\x00-\x7F])(?:$|[^a-zA-Z0-9\-_])"
)
AT_USERNAME_REGEX = re.compile(_AT_USERNAME_REGEX)

# backwards compatibility:
from .urls.github import FILE_URL_REGEX, SIMPLE_URL_REGEX
