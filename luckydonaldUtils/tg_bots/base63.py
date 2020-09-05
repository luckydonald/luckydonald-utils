from base64 import urlsafe_b64encode, urlsafe_b64decode
from luckydonaldUtils.encoding import to_native as n, to_binary as b
import re

REPLACEMENTS = {"-": "_0", "_": "_1"}


def revert_replacements(replacements):
    return {v: k for k, v in replacements.items()}
# end def


def multi_replace(string, replacements):
    """
    Given a string and a replacement map, it returns the replaced string.
    :param str string: string to execute replacements on
    :param dict replacements: replacement dictionary {value to find: value to replace}
    :rtype: str
    """
    # Place longer ones first to keep shorter substrings from matching where the longer ones should take place
    # For instance given the replacements {'ab': 'AB', 'abc': 'ABC'} against the string 'hey abc', it should produce
    # 'hey ABC' and not 'hey ABc'
    substrs = sorted(replacements, key=len, reverse=True)

    # Create a big OR regex that matches any of the substrings to replace
    regexp = re.compile('|'.join(map(re.escape, substrs)))

    # For each match, look up the new string in the replacements
    return regexp.sub(lambda match: replacements[match.group(0)], string)


def short_custom_base64_url_decode(base, encode_replacements=REPLACEMENTS):
    replacements = revert_replacements(encode_replacements)
    base = multi_replace(n(base), replacements)
    # add missing padding # http://stackoverflow.com/a/9807138
    return n(urlsafe_b64decode(base + '='*(4 - len(base)%4)))
# end def


def short_custom_base64_url_encode(string, encode_replacements=REPLACEMENTS):
    base = n(urlsafe_b64encode(b(string))).rstrip("=")
    return multi_replace(base, encode_replacements)
# end def

