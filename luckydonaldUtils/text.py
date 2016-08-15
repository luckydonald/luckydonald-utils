# -*- coding: utf-8 -*-
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


def split_in_parts(string, parts, strict=False):
    """
    Splits a string in given `parts` pieces.
    If string is a list, which has not exactly `parts` items, it will be joined and split afterwards.

    Examples:

      >>> split_in_parts('abc', 3)
      ['a', 'b', 'c']
      >>> split_in_parts('abcd', 3)
      ['a', 'bc', 'd']
      >>> split_in_parts('abcde', 3)
      ['ab', 'c', 'de']
      >>> split_in_parts('abcdef', 3)
      ['ab', 'cd', 'ef']
      >>>split_in_parts("abcdefgh", 3)
      ['abc', 'de', 'fgh']
      >>>split_in_parts('║╠╚ ', 4)
      ['║', '╠', '╚', ' ']
      >>>split_in_parts('ab', 4)
      ['', 'a', 'b', '']
      >>>split_in_parts('║╟╙╴⚠', 5)
      ['║', '╟', '╙', '╴', '⚠']

    :param string: the string to split
    :param parts: how many parts
    :param strict: if it should only have parts which are all same length.

    :return: list of strings
    """
    if isinstance(string, list):
        if len(string) == parts:
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


# end def
"""
        if len(text)> MAX_TEXT_LENGTH:
            last_space = text.rfind(" ", MAX_TEXT_LENGTH-40, MAX_TEXT_LENGTH)
            last_newline = text.rfind("\n", MAX_TEXT_LENGTH-40, MAX_TEXT_LENGTH)
            if abs(last_newline-last_space) < 20:
                split_at = last_newline
            else:
                split_at = last_space
            assert split_at <= MAX_TEXT_LENGTH
            self.text = text[:split_at]
            next_text = text[split_at+1:] # omit the space or newline.
            logger.debug("Splitted {num} character long message text to {len_a} and {len_b}.".format(
                num=len(text), len_a=len(self.text), len_b=len(next_text)))
            self._next_msg = TextMessage(next_text, receiver)
"""


def is_sentence_end(char):
    return char in ".?!"


def is_sentence_part_end(char):
    return char in ",:;"


def is_word_separator(char):
    return char in [" ", "\n", ".", ",", "?", "!", "@", "#", "$", ":", ";", "-", "<", ">", "[", "]", "(", ")", "{", "}",
                    "=", "/", "+", "%", "&", "^", "*", "'", "\"", "`", "~", "|"]


def escape(string):
    for i in range(0, 7):
        string = string.replace(CHARS_UNESCAPED[i], CHARS_ESCAPED[i])
    return string
