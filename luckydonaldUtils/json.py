# -*- coding: utf-8 -*-
from datetime import datetime
from . import py2

__author__ = 'luckydonald'


def to_jsonable_dict(skip_keys=list()):
    dict(to_jsonable_dict(skip_keys=skip_keys))

if py2:
    def to_jsonable_dict_iterator(dict, skip_keys=list()):
        for key, value in dict.iteritems():
            if key in skip_keys:
                continue
            if isinstance(value, datetime):
                yield (key, str(value.isoformat()))
            else:
                yield (key, value)
else:
    def to_jsonable_dict_iterator(dict, skip_keys=list()):
        for key, value in dict.items():
            if key in skip_keys:
                continue
            if isinstance(value, datetime):
                yield (key, str(value.isoformat()))
            else:
                yield (key, value)