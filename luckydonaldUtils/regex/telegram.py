# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)
import re

_USERNAME_REGEX = '[a-zA-Z](?:[a-zA-Z0-9]|_(?!_)){3,30}[a-zA-Z0-9]'  # https://regex101.com/r/nZdOHS/2
USERNAME_REGEX = re.compile(_USERNAME_REGEX)

_TELEGRAM_DOMAIN_REGEX = '(?:https?://)?(?:t(?:lgrm)?\.me|telegram\.(?:me|dog))/'
TELEGRAM_DOMAIN_REGEX = re.compile(_TELEGRAM_DOMAIN_REGEX)

_USER_LINK_REGEX = '(?P<domain>' + _TELEGRAM_DOMAIN_REGEX + ')(?P<username>' + _USERNAME_REGEX + ')'
USER_LINK_REGEX = re.compile(_USER_LINK_REGEX)

_USER_AT_REGEX = '@(?P<username>' + _USERNAME_REGEX + ')'
USER_AT_REGEX = re.compile(_USER_AT_REGEX)

_FULL_USERNAME_REGEX = '(?P<prefix>(?P<domain>' + _TELEGRAM_DOMAIN_REGEX + ')|@)(?P<username>' + _USERNAME_REGEX + ')'
FULL_USERNAME_REGEX = re.compile(_FULL_USERNAME_REGEX)
