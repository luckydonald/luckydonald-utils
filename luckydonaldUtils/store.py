# -*- coding: utf-8 -*-

import base64
from .dependencies import import_or_install
# from usersettings import Settings
Settings = import_or_install("usersettings.Settings", "usersettings")  # pip install usersettings
# from Crypto import Random
Random = import_or_install("Crypto.Random", "pycrypto")   # pip install pycrypto
# from Crypto.Cipher import AES
AES = import_or_install("Crypto.Cipher.AES", "pycrypto")  # pip install pycrypto
# from Crypto.Hash import MD5
MD5 = import_or_install("Crypto.Hash.MD5", "pycrypto")    # pip install pycrypto

__author__ = 'luckydonald'

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
un_pad = lambda s: s[:-ord(s[len(s) - 1:])]


class Store(object):
    def __init__(self, settings_name, key=None):
        if not key:
            settings = Settings(settings_name)  # store settings, password etc.
            settings.add_setting("do-not-change!", str, random())
            settings.load_settings()
            settings.save_settings()
            self.key = settings.get("do-not-change!")
        else:
            self.key = key

    def encrypt(self, raw):
        raw = pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return un_pad(cipher.decrypt(enc[16:]))


def random():
    return MD5.new(Random.new().read(4)).hexdigest()
