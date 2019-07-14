# -*- coding: utf-8 -*-
from random import choice
from .quotes import get_quote
from .ponies import WAIFU

__author__ = 'luckydonald'


def get_headers(language="en"):
    headers = {}
    headers["Server"] = choice(["iPod Touch, iOS 2.3.2", "Banana 0.2", "KONICHIWA/1.0", "'; DROP TABLE servertypes; -"])
    headers["X-Powered-By"] = choice(["Magical Ponies", "Rats in our Basement", "Unicorns", "Friendship", "TONS OF SUGAR", "coffee", "Bananas and Rum"])
    headers["X-Best-Pony"] = choice(WAIFU)
    headers["X-Answer"] = "42"
    headers["X-Never-Gonna"] = "Give you up."
    headers["X-Nananana"] = "Batman!"
    headers["X-Message"] = get_quote(language)
    return headers
