# -*- coding: utf-8 -*-
import re

__author__ = 'luckydonald'
__all__ = [
    'USERNAME_REGEX', '_USERNAME_REGEX', 'USER_AT_REGEX', '_USER_AT_REGEX',
    'FULL_USERNAME_REGEX', '_FULL_USERNAME_REGEX'
]

_USERNAME_REGEX = '[a-zA-Z](?:[a-zA-Z0-9]|_(?!_)){3,30}[a-zA-Z0-9]'  # https://regex101.com/r/nZdOHS/2
USERNAME_REGEX = re.compile(_USERNAME_REGEX)

_USER_AT_REGEX = '@(?P<username>' + _USERNAME_REGEX + ')'
USER_AT_REGEX = re.compile(_USER_AT_REGEX)

from .urls.telegram import _TELEGRAM_DOMAIN_REGEX
_FULL_USERNAME_REGEX = '(?P<prefix>(?P<domain>' + _TELEGRAM_DOMAIN_REGEX + ')|@)(?P<username>' + _USERNAME_REGEX + ')'
FULL_USERNAME_REGEX = re.compile(_FULL_USERNAME_REGEX)

# backwards compatibility:
from .urls.telegram import TELEGRAM_DOMAIN_REGEX, _USER_LINK_REGEX, USER_LINK_REGEX
