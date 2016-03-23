# -*- coding: utf-8 -*-
import unittest
from collections import OrderedDict

from luckydonaldUtils.regex.github import FILE_URL_REGEX, AT_USERNAME_REGEX
__author__ = 'luckydonald'


class Test(unittest.TestCase):
    """
    Tests if the Regex matches only the right urls.
    """
    # input url and permanent url of that. None, if not supposed to match.
    # Lol, the permanent URLs can/will change. Should setup a extra repo for testing this.
    urls_to_test = OrderedDict()
    urls_to_test["https://github.com/luckydonald/pytg/issues/72"] = None
    urls_to_test["https://github.com/luckydonald/pytg"] = "https://github.com/luckydonald/pytg/tree/ed8d622a06fd24ec75c0c301984fa6d58ebd6e61"
    urls_to_test["https://github.com/luckydonald/pytg/"] = "https://github.com/luckydonald/pytg/tree/ed8d622a06fd24ec75c0c301984fa6d58ebd6e61"
    urls_to_test["https://github.com/luckydonald/pytg/blob/master/.gitmodules"] = "https://github.com/luckydonald/pytg/blob/ed8d622a06fd24ec75c0c301984fa6d58ebd6e61/.gitmodules"
    urls_to_test["https://github.com/luckydonald/pytg/tree/development"] = "https://github.com/luckydonald/pytg/tree/4e68eb7a13f19efe74994dcf54b9ef01de8bae3b"
    urls_to_test["https://github.com/luckydonald/pytg/tree/issue%233"] = "https://github.com/luckydonald/pytg/tree/35293c98be83672d9384c751cff7e40d7590e158"
    urls_to_test["https://github.com/luckydonald/pytg/blob/issue%233/.gitignore"] = "https://github.com/luckydonald/pytg/blob/35293c98be83672d9384c751cff7e40d7590e158/.gitignore"
    urls_to_test["https://github.com/luckydonald/pytg/blob/35293c98be83672d9384c751cff7e40d7590e158/.gitignore"] = "https://github.com/luckydonald/pytg/blob/35293c98be83672d9384c751cff7e40d7590e158/.gitignore"
    urls_to_test["https://github.com/notifications"] = None
    urls_to_test["https://github.com/luckydonald/pytg/commit/8c62dc4a35ef4ff2b81f4c0801f5448374fccaa1"] = None
    urls_to_test["https://github.com/luckydonald/pytg/pull/61/commits"] = None
    urls_to_test["https://github.com/huiyiqun/pytg/blob/e3790d9c2188949991295580f4f06d6f228ad082/pytg/fix_msg_array.py"] = "https://github.com/huiyiqun/pytg/blob/e3790d9c2188949991295580f4f06d6f228ad082/pytg/fix_msg_array.py"

    user_to_test = OrderedDict()
    user_to_test["@luckydonald"] = "luckydonald"
    user_to_test["luckydonald"] = None  # no @
    user_to_test["@with_at"] = None     # _ not allowed.
    user_to_test["without_at"] = None   # no @
    user_to_test["@bonbot"] = "bonbot"
    user_to_test["@sweetiebot"] = "sweetiebot"
    user_to_test["@mlfwbot"] = "mlfwbot"
    user_to_test["@mylittlefacewhenbot"] = "mylittlefacewhenbot"
    user_to_test["@example123"] = "example123"
    user_to_test["@look_i_have_a_username"] = None
    user_to_test["@and_more"] = None
    user_to_test["@bot_username_bot"] = None
    user_to_test["@pollbot"] = "pollbot"
    user_to_test["@gif"] = "gif"
    user_to_test["@vid"] = "vid"
    user_to_test["@pic"] = "pic"
    user_to_test["@bing"] = "bing"
    user_to_test["@wiki"] = "wiki"
    user_to_test["@imdb"] = "imdb"
    user_to_test["@bold"] = "bold"
    user_to_test["@_illegal"] = None
    user_to_test["@not__allowed"] = None
    user_to_test["@illegal_2_"] = None
    user_to_test["@404not_allowed_either"] = None
    user_to_test["@-illegal"] = None
    user_to_test["@not--allowed"] = None
    user_to_test["@illegal-2-"] = None
    user_to_test["@404Actually-allowed"] = "404Actually-allowed"
    user_to_test["@abcd"] = "abcd"
    user_to_test["@at/whats up"] = "at"
    user_to_test["@@bot"] = None
    user_to_test["@bothey@"] = "bothey"
    user_to_test["@mööüpasd"] = None
    user_to_test["@this_is_valit_until_#here"] = None
    user_to_test["@test.hey"] = "test"
    user_to_test["mail@example.com"] = None
    user_to_test["mail @example.com"] = "example"
    user_to_test["hey.@exple.How are you?I am fine!"] = "exple"  # yeah, that's a typo
    user_to_test["\@escaped_not_a_user"] = None

    def test_github_links(self):
        for input, output in self.urls_to_test.items():
            result = FILE_URL_REGEX.search(input)
            print ("\nInput   : {inp}\nexpected: {exp}\ngot     : {got}".format(inp=input, exp="MATCH" if output else "None", got=result))
            if output is None:
                self.assertIsNone(result, msg="Should not find anything.")
            else:
                self.assertIsNotNone(result, msg="Should find a url.")
            # end if
        # end for
    # end def

    def test_github_link_match_groups(self):
        input = "https://github.com/luckydonald/luckydonald-utils/blob/3888e7e6967e8b9b80245300321ddd2c19eff391/" \
                "luckydonaldUtils/eastereggs/headers.py#L12-L13"
        m = FILE_URL_REGEX.match(input)
        print(repr(m.groupdict()))
        self.assertEqual(m.group("user"),    "luckydonald", "user")
        self.assertEqual(m.group("repo"),    "luckydonald-utils", "repo")
        self.assertIn("path", m.groupdict(), "path")
        self.assertEqual(m.group("path"),    "blob/3888e7e6967e8b9b80245300321ddd2c19eff391/luckydonaldUtils/eastereggs/headers.py", "path")
        self.assertEqual(m.group("kind"),    "blob", "kind")
        self.assertEqual(m.group("branch"),  "3888e7e6967e8b9b80245300321ddd2c19eff391", "branch")
        self.assertEqual(m.group("file"),    "luckydonaldUtils/eastereggs/headers.py", "file")
        self.assertIn("hash", m.groupdict(), "hash")
        self.assertEqual(m.group("hash"),    "L12-L13", "hash")
    # end def

    def test_user_regex(self):
        for input, output in self.user_to_test.items():
            result = AT_USERNAME_REGEX.search(input)
            print ("\nInput   : {inp}\nexpected: {exp}\ngot     : {got}".format(inp=input, exp=output, got=result.group("user") if result else None))
            if output is None:
                self.assertIsNone(result, msg="Should not find anything.")
            else:
                self.assertEqual(output, result.group("user"), msg="Should find a @user.")
            # end if
        # end for
# end class

