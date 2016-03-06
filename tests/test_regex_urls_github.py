# -*- coding: utf-8 -*-
import unittest
from collections import OrderedDict

from luckydonaldUtils.regex.github import FILE_URL_REGEX
__author__ = 'luckydonald'


class Test(unittest.TestCase):
    """
    Tests if the Regex matches only the right urls.
    """
    # input url and permanent url of that. None, if not supposed to match.
    # Lol, the permanent URLs can/will change. Should setup a extra repo for testing this.
    tests = OrderedDict()
    tests["https://github.com/luckydonald/pytg/issues/72"] = None
    tests["https://github.com/luckydonald/pytg"] = "https://github.com/luckydonald/pytg/tree/ed8d622a06fd24ec75c0c301984fa6d58ebd6e61"
    tests["https://github.com/luckydonald/pytg/"] = "https://github.com/luckydonald/pytg/tree/ed8d622a06fd24ec75c0c301984fa6d58ebd6e61"
    tests["https://github.com/luckydonald/pytg/blob/master/.gitmodules"] = "https://github.com/luckydonald/pytg/blob/ed8d622a06fd24ec75c0c301984fa6d58ebd6e61/.gitmodules"
    tests["https://github.com/luckydonald/pytg/tree/development"] = "https://github.com/luckydonald/pytg/tree/4e68eb7a13f19efe74994dcf54b9ef01de8bae3b"
    tests["https://github.com/luckydonald/pytg/tree/issue%233"] = "https://github.com/luckydonald/pytg/tree/35293c98be83672d9384c751cff7e40d7590e158"
    tests["https://github.com/luckydonald/pytg/blob/issue%233/.gitignore"] = "https://github.com/luckydonald/pytg/blob/35293c98be83672d9384c751cff7e40d7590e158/.gitignore"
    tests["https://github.com/luckydonald/pytg/blob/35293c98be83672d9384c751cff7e40d7590e158/.gitignore"] = "https://github.com/luckydonald/pytg/blob/35293c98be83672d9384c751cff7e40d7590e158/.gitignore"
    tests["https://github.com/notifications"] = None
    tests["https://github.com/luckydonald/pytg/commit/8c62dc4a35ef4ff2b81f4c0801f5448374fccaa1"] = None
    tests["https://github.com/luckydonald/pytg/pull/61/commits"] = None
    tests["https://github.com/huiyiqun/pytg/blob/e3790d9c2188949991295580f4f06d6f228ad082/pytg/fix_msg_array.py"] = "https://github.com/huiyiqun/pytg/blob/e3790d9c2188949991295580f4f06d6f228ad082/pytg/fix_msg_array.py"

    def test_github_links(self):
        for input, output in self.tests.items():
            result = FILE_URL_REGEX.search(input)
            print ("\nInput   : {inp}\nexpected: {exp}\ngot     : {got}".format(inp=input, exp=output, got=result))
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
# end class

