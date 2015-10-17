# -*- coding: utf-8 -*-
from random import randint

__author__ = 'luckydonald'

def get_headers():
	headers = []
	headers["Server"] = ["iPod Touch, iOS 2.3.2", "KONICHIWA/1.0", "'; DROP TABLE servertypes; -", "Banana 0.2"][randint(0,3)]
	headers["X-Powered-By"] = ["Magical Ponies", "Rats in our Basement", "Unicorns", "Friendship", "TONS OF SUGAR", "coffee", "Bananas and Rum"][randint(0,6)]
	headers["X-Best-Pony"] = "Littlepip"
	headers["X-Answer"] = "42"
	headers["X-Never-Gonna"] = "Give you up."
	headers["X-Nananana"] = "Batman!"
	return headers