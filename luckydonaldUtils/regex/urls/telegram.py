# -*- coding: utf-8 -*-
import re

__author__ = 'luckydonald'
__all__ = ['TELEGRAM_DOMAIN_REGEX', '_TELEGRAM_DOMAIN_REGEX', 'USER_LINK_REGEX', '_USER_LINK_REGEX']

_TELEGRAM_DOMAIN_REGEX = '(?:https?://)?(?:t(?:lgrm)?\.me|telegram\.(?:me|dog))/'
TELEGRAM_DOMAIN_REGEX = re.compile(_TELEGRAM_DOMAIN_REGEX)

from ..telegram import _USERNAME_REGEX

_USER_LINK_REGEX = '(?P<domain>' + _TELEGRAM_DOMAIN_REGEX + ')(?P<username>' + _USERNAME_REGEX + ')'
USER_LINK_REGEX = re.compile(_USER_LINK_REGEX)
