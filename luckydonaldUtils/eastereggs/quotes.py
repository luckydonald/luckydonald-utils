# -*- coding: utf-8 -*-
"""
NOT PY2 ready!
>>> from luckydonaldUtils.eastereggs.quotes import get_quote
>>> get_quote("de")
>>> get_quote()
"""

from random import randint
from ..dependencies import import_or_install
import_or_install("weakreflist", "weakreflist")
from weakreflist.weakreflist import WeakList  # pip install weakreflist

__author__ = 'luckydonald'


QUOTES = [
	"Littlepip is best pony!",
	{"en": "May contain nuts", "de": "Kann Spuren von Nüssen enthalten"},
	{"en": "0% sugar", "de": "0% Zucker"},
	{"en": "100% pure", "de":"100% rein"},
	{"en": "12345 is a bad password","de": "12345 ist ein schlechtes Passwort"},
	"90% bug free!",
	{"en": "Any computer is a laptop if you're brave enough", "de":"Jeder Computer ist ein Laptop, wenn du mutig bist"},
	"As seen on TV",
	"Ask your doctor",
	"Awesome",
	"20% cooler",
	"Muffins!",
	"Classy",
	"Do not distribute",
	"Don't look directly at the bugs",
	"Free dental included",
	"Gasp!",
	{"de": "Keuch!"},
	"Google anlyticsed!",
	{"en": "Günter was here", "de": "Günter war hier"},
	"Hot tamale, hot hot tamale!",
	"Now in 3D",
	"Coded in Python 3",
	{"en": "Lives in a pineapple under the sea", "de": "Wohnt in 'ner Ananas ganz tief im Meer"},
	"Limited edition!",
	"Keep calm and carry on",
	{"de": "Nicht nur sauber sondern rein"},
	{"de": "Mit 99% weniger Zucker", "en":"With 99% less sugar"},
	{"de": "Besser als herkömmliche Produkte"},
	{"en": "Supercalifragilisticexpialidocious", "de":"Superkalifragilisticexpialigetisch"},
	"War. War never changes.",
	{"en": "The sky is the limit", "de":"Alles ist möglich"},
	{"en": "Turing complete", "de": "Turing-vollständig"},
	"Ultimate edition",
	{"en": "Uninflammable", "de": "Nicht brennbar"},
	{"en": "Water proof", "de": "Wasserdicht"},
	{"en": "Vote for net neutrality!", "de": "Stimme für die Netzneutralität!"},
	{"de": "Unplattbar"},
	"What's up, Doc?",
	{"en": "You can't explain that", "de": "Das kannst du nicht erklären"},
	"Multithreaded",
	"0xffffff",
	{"en": "#c0ffee is not a brown color", "de": "Die Farbe #c0ffee ist nicht braun."},
	{"en": "Cooler than Spock", "de": "Cooler als Spock"},
	{"de": "Achten Sie auf die Goldkante, es lohnt sich."},
	{"de": "Afri-Cola überwindet den toten Punkt."},
	{"de": "Dahinter steckt immer ein kluger Kopf."},
	{"de": "Mach mal Pause..."},
	{"de": "Dieses Produkt ist Glutenfrei."},
	{"de": "Milch macht müde Männer munter"},
	{"de": "Zu Risiken und Nebenwirkungen fragen Sie ihren Arzt oder Apotheker"},
	{"de": "Jetzt mit mehr Vitaminen"},
	{"de": "Hier könnte Ihre Werbung stehen"},
	"Pon <3",
	{"en":"Pon3 is best musician"},
	{"en":"Batteries not included.", "de": "Batterien nicht enthalten"},
	{"de": "Abbildung ähnlich"},
	{"de": "Serviervorschlag"},
	{"en": "So kawaii"},
	"Aloha",
	{"de": "Anscheinend können Sie lesen", "en": "It seems you can read"},
	"DINKELBERG!",
	#{"de": ".sträwkcür tsi txeT reseiD", "en": ".desrever si txet sihT"},
	"The cake is a lie",
	#{"de": ""},
	#{"en": "", "de": ""},
]
QUOTES_BY_LANGUAGE = {"en": WeakList()}


""" Store them ordered. """
for quote in QUOTES:
	if isinstance(quote, dict):
		for language, text in quote.items():  # todo: python 2 iter_something()
			if not language in QUOTES_BY_LANGUAGE:
				QUOTES_BY_LANGUAGE[language] = WeakList()
			#end if
			QUOTES_BY_LANGUAGE[language].append(quote[language])
		#end for
	#end if
#end for
for quote in QUOTES:
	if isinstance(quote, str):
		for language in QUOTES_BY_LANGUAGE.keys():  # todo: py2:viewkeys():
			QUOTES_BY_LANGUAGE[language].append(quote)
		#end for
	#end if
#end for


def get_quote(language="en"):
	"""
	Get a random quote.

	:param language: default: "en"
	:return:
	"""
	qs = QUOTES_BY_LANGUAGE[language]
	return qs[randint(0, len(qs)-1)]
#end def
