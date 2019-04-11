# -*- coding: utf-8 -*-
from typing import Union, Any, List, Dict

# from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'
__all__ = ["JSONType"]

# logger = logging.getLogger(__name__)


# define a type for the returned stuff of parsed JSON,
# at least until the fine folks at https://github.com/python/typing/issues/182 find a solution.
JSONType = Union[None, bool, int, float, str, List[Any], Dict[str, Any]]
# JSONType = Union[None, bool, int, float, str, List['JSONType'], Dict[str, 'JSONType']]  # someday recursive might work


