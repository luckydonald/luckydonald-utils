# -*- coding: utf-8 -*-
from collections import defaultdict

__author__ = 'luckydonald'


def etree_to_dict(t):
    """
    Function to modify a xml.etree.ElementTree thingy to be a dict.
    Attributes will be accessible via ["@attribute"],
    and get the text (aka. content) inside via ["#text"]

    TESTED ONLY FOR PYTHON 3! (but should be working in Python 2...)
    :param t:
    :return:
    """
    # THANKS http://stackoverflow.com/a/10077069

    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}  # .items() is bad for python 2
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())  # .items() is bad for python 2
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d
