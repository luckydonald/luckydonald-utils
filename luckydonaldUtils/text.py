# -*- coding: utf-8 -*-
import re
try:
    from .encoding import binary_type, text_type
except (ImportError, SystemError):
    # non-relative imports to enable doctests
    from luckydonaldUtils.encoding import binary_type, text_type
# end if

__author__ = 'luckydonald'

CHARS_UNESCAPED = ["\\", "\n", "\r", "\t", "\b", "\a", "'"]
CHARS_ESCAPED = ["\\\\", "\\n", "\\r", "\\t", "\\b", "\\a", "\\'"]


def text_split(text, limit, max_parts=None):
    """
    Split a text, each part less or equal to `limit`. Prefer splitting at linebreaks, sentences and lastly words.

    :type text: str
    :type limit: int
    :param max_parts: If not None: In how many parts it should be split.
                      The last element might be longer as the given limit.
    :type  max_parts: None | int
    :return:
    """
    if not isinstance(text, str):
        raise TypeError("text is not str but {}".format(type(text)))
    assert isinstance(limit, int)
    assert max_parts is None or isinstance(max_parts, int)
    text = text.strip()
    if len(text) == 0 or limit == 0:
        return []
    if max_parts == 1:
        return [text]
    assert max_parts is None or max_parts > 1
    # LinkRanges lnkRanges = textParseLinks(text, TextParseLinks | TextParseMentions | TextParseHashtags);
    # currentLink = 0
    # lnkCount = lnkRanges.size()
    half = limit // 2
    good_level = 0
    good = 0
    end = len(text)
    unicode_i = 0
    for i in range(0, end):
        char = text[i]
        # while (currentLink < lnkCount && ch >= lnkRanges[currentLink].from + lnkRanges[currentLink].len) {
        # 	++currentLink;
        #  }
        # bool inLink = (currentLink < lnkCount) && (ch > lnkRanges[currentLink].from) &&
        #   (ch < lnkRanges[currentLink].from + lnkRanges[currentLink].len);
        if unicode_i > half:
            if char == "\n":
                if i + 1 < end and text[i + 1] == "\n" and good_level <= 7:
                    good_level = 7
                    good = i
                elif good_level <= 6:
                    good_level = 6
                    good = i
            elif char.isspace():
                if is_sentence_end(char) and good_level <= 5:
                    good_level = 5
                    good = i
                elif is_sentence_part_end(text[i - 1]) and good_level <= 4:
                    good_level = 4
                    good = i
                elif good_level <= 3:
                    good_level = 3
                    good = i
            elif is_word_separator(text[i - 1]) and good_level <= 2:
                good_level = 2
                good = i
            elif good_level <= 1:
                good_level = 1
                good = i
                # end if
        # end if
        if unicode_i >= limit:
            if max_parts == 1:
                return [text.strip()]
            first_text = text[:good]
            text = text[good:]
            parts = [first_text.strip(), ]
            if max_parts is None:
                parts.extend(text_split(text, limit))
            elif max_parts > 1:
                parts.extend(text_split(text, limit, max_parts=max_parts - 1))
            else:
                raise ArithmeticError("max_split reached illegal state: {}".format(max_parts))
            return parts
        # end if
        if char in CHARS_UNESCAPED:
            unicode_i += 2
        else:
            unicode_i += len(char.encode('utf-8'))
    # end for
    return [text]
# end def


def is_sentence_end(char):
    return char in ".?!"
# end def


def is_sentence_part_end(char):
    return char in ",:;"
# end def


def is_word_separator(char):
    return char in [
        " ", "\n", ".", ",", "?", "!", "@", "#", "$", ":", ";", "-", "<", ">", "[", "]",
        "(", ")", "{", "}", "=", "/", "+", "%", "&", "^", "*", "'", "\"", "`", "´", "„", "”", "~", "|"
    ]
# end def


def split_in_parts(string, parts, strict=False):
    """
    Splits a string in `parts` amount of pieces.
    If `string` is a :class:`list`, which has not exactly `parts` items, it will be joined and split afterwards.

    Examples:

      >>> split_in_parts('abc', 3)
      ['a', 'b', 'c']
      >>> split_in_parts('abcd', 3)
      ['a', 'bc', 'd']
      >>> split_in_parts('abcde', 3)
      ['ab', 'c', 'de']
      >>> split_in_parts('abcdef', 3)
      ['ab', 'cd', 'ef']
      >>> split_in_parts("abcdefgh", 3)
      ['abc', 'de', 'fgh']
      >>> split_in_parts('║╠╚ ', 4)
      ['║', '╠', '╚', ' ']
      >>> split_in_parts('ab', 4)
      ['', 'a', 'b', '']
      >>> split_in_parts('ab', 3)
      ['a', '', 'b']
      >>> split_in_parts('║╟╙╴⚠', 5)
      ['║', '╟', '╙', '╴', '⚠']
      
      >>> split_in_parts(['a','b','c'], 3)  # list with right amount of parts, unchanged
      ['a', 'b', 'c']
      >>> split_in_parts(['aa','b','c'], 3)  # list with  right amount of parts, unchanged
      ['aa', 'b', 'c']
      >>> split_in_parts(['a','b','c','d'], 3)  # list with wrong amount of parts, joined + splitted
      ['a', 'bc', 'd']
      >>> split_in_parts(['aa','b','c','d'], 3)  # list with wrong amount of parts, joined + splitted
      ['aa', 'b', 'cd']
      
      >>> split_in_parts([], 0)  # empty list with right amount of parts, unchanged
      []
      >>> split_in_parts([], 1)  # empty list with wrong amount of parts, empty string generated
      ['']
      >>> split_in_parts([], 2)  # empty list with wrong amount of parts, empty string generated
      ['', '']
      
      >>> split_in_parts("abc", 3, strict=True)  # strict mode, fitting `parts` parameter
      ['a', 'b', 'c']
      >>> split_in_parts("abc", 4, strict=True)  # strict mode, wrong `parts` parameter
      Traceback (most recent call last):
      ...
      ValueError: In strict mode you need a string which can be split in 4 equal pieces.
      >>> split_in_parts("abcdef", 2, strict=True)  # strict mode, wrong `parts` parameter
      ['abc', 'def']
      
      >>> split_in_parts(['a','b','c'], 3, strict=True)  # list with right amount of parts, unchanged
      ['a', 'b', 'c']
      >>> split_in_parts(['aa','b','c'], 3, strict=True)  # list with  right amount of parts, but not equal length
      Traceback (most recent call last):
      ...
      ValueError: In strict mode you need a list where all 3 items have equal length.
      >>> split_in_parts(['aaa','bbb','ccc','ddd'], 3, strict=True)  # list with wrong amount of parts, joined + splitted
      ['aaab', 'bbcc', 'cddd']
      >>> split_in_parts(['aa','b','c','d'], 3, strict=True)  # list with wrong amount of parts, joined + splitted
      Traceback (most recent call last):
      ...
      ValueError: In strict mode you need a string which can be split in 3 equal pieces.
    
      >>> split_in_parts([], 0, strict=True)  # empty list with right amount of parts, unchanged
      []
      >>> split_in_parts([], 1, strict=True)  # empty list with wrong amount of parts, empty string generated
      ['']
      >>> split_in_parts([], 2, strict=True)  # empty list with wrong amount of parts, empty string generated
      ['', '']
      

    :param string: the string to split
    :param parts: how many parts
    :param strict: if it should only have parts which are all same length.

    :return: list of strings
    """
    if isinstance(string, list):
        if len(string) == parts:
            if strict and len(string) != 0:
                length = len(string[0])
                if any(len(item) != length for item in string):  # length wrong in some element
                    raise ValueError("In strict mode you need a list where all {parts} items have equal length.".format(
                        parts=parts
                    ))
                    # end if  length wrong
            # end if strict
            return string
        # end if
        string = "".join(string)
    # end if
    length = len(string)
    slice_size = length / parts
    if strict and length % parts != 0:
        raise ValueError("In strict mode you need a string which can be split in {parts} equal pieces.".format(
            parts=parts
        ))
    # end if
    part_pos = [0]
    for i in range(0, parts):  # parts = 3 -> for [1, 2]
        part_pos.append(round(slice_size * (i + 1)))
    # end for
    # print(part_pos)
    part_pos[1] = round(part_pos[1])
    strings = []
    for i in range(parts):
        strings.append(string[part_pos[i]:part_pos[i + 1]])
    # end for
    return strings
# end def


def escape(string):
    for i in range(0, 7):
        string = string.replace(CHARS_UNESCAPED[i], CHARS_ESCAPED[i])
    return string
# end def


def cut_paragraphs(text, length=200) -> str:
    """
    This limits a paragraph to a given length.
    :param text:
    :param length:
    :return:
    """
    if len(text) == length:
        return text
    short = text[:length]
    last_sentence_ending = max(short.rfind(x) for x in ["\n", "...", ";", ":", "!", "?", "."])
    if last_sentence_ending > 0 and length - last_sentence_ending < 20:  # limit it to max. removing 20 characters,
        # else try something different.
        return short[:last_sentence_ending + 1]
    from .holder import Holder
    h = Holder()
    if h(short.rfind(",", 0, -3)) > 0 and h() < length - 3:
        return short[:h() + 1] + "..."
    if h(short.rfind(" ", 0, -3)) > 0:
        return short[:h()] + "..."
    # fallback if nothing splittable was found.
    return text[:-3] + "..."  # will just cut it.
# end def


def lcut(input_string, part_to_cut):
    """
    Cuts away a `part_to_cut` from the beginning of the `input_string`.
    If your `input_string` is no text type, it will be returned unchanged.
    
    
    Examples: 
        
        >>> lcut("foobar", "foo")
        'bar'
        
        >>> lcut("foobar", "batz")
        'foobar'
        
        >>> lcut(False, "False")
        False
        
        >>> lcut(u"foobar", u"foo") == u"bar"  # unicode
        True
        
        >>> lcut(b"foobar", b"foo") == b"bar"  # binary
        True
        
        >>> lcut(b"foobar", u"foo") == b"bar"  # binary vs unicode  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        TypeError: startswith first arg must be bytes or a tuple of bytes, not str

    
    :param input_string: Your complete string you want to cut stuff from
    :param part_to_cut: What you want to cut away from the start, if found.
    :return: 
    """
    if not isinstance(input_string, (text_type, binary_type)):  # non-text
        return input_string
    # end if
    if input_string.startswith(part_to_cut):
        return input_string[len(part_to_cut):]
    # end if
    return input_string
# end def


def rcut(input_string, part_to_cut):
    """
    Cuts away a `part_to_cut` from the end of the `input_string`.
    If your `input_string` is no text type, it will be returned unchanged.
    
    
    Examples: 
        
        >>> rcut("foobar", "bar")
        'foo'
        
        >>> rcut("foobar", "batz")
        'foobar'
        
        >>> rcut(False, "False")
        False
        
        >>> rcut(u"foobar", u"bar") == u"foo"  # unicode
        True
        
        >>> rcut(b"foobar", b"bar") == b"foo"  # binary
        True
        
        >>> rcut(b"foobar", u"bar") == b"foo"  # binary vs unicode  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        TypeError: endswith first arg must be bytes or a tuple of bytes, not str


    :param input_string: Your complete string you want to cut stuff from
    :param part_to_cut: What you want to cut away from the start, if found.
    :return: 
    """
    if not isinstance(input_string, (text_type, binary_type)):  # non-text
        return input_string
    # end if
    if input_string.endswith(part_to_cut):
        return input_string[:len(part_to_cut)]
    # end if
    return input_string
# end def


def cut(input_string, part_to_cut):
    return lcut(rcut(input_string, part_to_cut), part_to_cut)


# end def


def convert_to_underscore(name):
    """
    'someFunctionWhateverMateYoLOLLel' -> 'some_Function_Whatever'

    >>> convert_to_underscore('test123isThisWorkingXXX')
    'test_123_is_This_Working_XXX'

    >>> convert_to_underscore('XXXNightmaremoonXXX')
    'XXX_Nightmaremoon_XXX'

    >>> convert_to_underscore('Hunter2')
    'Hunter_2'

    >>> convert_to_underscore('HDMI2GardenaGartenschlauchAdapter')
    'HDMI_2_Gardena_GartenschlauchAdapter'

    >>> convert_to_underscore('test23')
    'test_23'

    >>> convert_to_underscore('LEL24')
    'LEL_24'

    >>> convert_to_underscore('LittlepipIsBestPony11111')
    'Littlepip_Is_Best_Pony_11111'

    >>> convert_to_underscore('4458test')
    '4458_test'

    >>> convert_to_underscore('4458WUT')
    '4458_WUT'

    >>> convert_to_underscore('xXx4458xXx')
    'x_Xx_4458_x_Xx'

    >>> convert_to_underscore('XxX4458XxX')
    'Xx_X_4458_Xx_X'

    """
    RE_c_0 = re.compile(r'([A-Za-z])([0-9]+)')
    RE_0_c = re.compile(r'([0-9]+)([A-Za-z])')
    RE_x_Cc = re.compile(r'([^0-9])([A-Z][a-z0-9]+)')
    RE_c_C = re.compile(r'([a-z0-9])([A-Z])')

    # print = str
    # print(1, name)
    name = RE_c_0.sub(r'\1_\2', name)
    # print(2, name)
    name = RE_0_c.sub(r'\1_\2', name)
    # print(3, name)
    name = RE_x_Cc.sub(r'\1_\2', name)
    # print(4, name)
    name = RE_c_C.sub(r'\1_\2', name)
    # print(5, name)
    return name
# end def
