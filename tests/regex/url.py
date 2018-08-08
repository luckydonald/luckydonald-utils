import sys

import unittest
from luckydonaldUtils.regex.urls import URL_REGEX


class MyTestCase(unittest.TestCase):
    VALID = [
        "http://✪df.ws/123",
        "http://userid:password@example.com:8080",
        "http://userid:password@example.com:8080/",
        "http://userid@example.com",
        "http://userid@example.com/",
        "http://userid@example.com:8080",
        "http://userid@example.com:8080/",
        "http://userid:password@example.com",
        "http://userid:password@example.com/",
        "http://142.42.1.1/",
        "http://142.42.1.1:8080/",
        "http://➡.ws/䨹",
        "http://⌘.ws",
        "http://⌘.ws/",
        "http://foo.com/blah_(wikipedia)#cite-1",
        "http://foo.com/blah_(wikipedia)_blah#cite-1",
        "http://foo.com/unicode_(✪)_in_parens",
        "http://foo.com/(something)?after=parens",
        "http://☺.damowmow.com/",
        "http://code.google.com/events/#&product=browser",
        "http://j.mp",
        "ftp://foo.bar/baz",
        "http://foo.bar/?q=Test%20URL-encoded%20stuff",
        "http://مثال.إختبار",
        "http://例子.测试"
    ]
    INVALID = [
        "http://",
        "http://.",
        "http://..",
        "http://../",
        "http://?",
        "http://??",
        "http://??/",
        "http://#",
        "http://##",
        "http://##/",
        "http://foo.bar?q=Spaces should be encoded",
        "//",
        "//a",
        "///a",
        "///",
        "http:///a",
        "foo.com",
        "rdar://1234",
        "h://test",
        "http:// shouldfail.com",
        ":// should fail",
        "http://foo.bar/foo(bar)baz quux",
        "ftps://foo.bar/",
        "http://-error-.invalid/",
        "http://a.b--c.de/",
        "http://-a.b.co",
        "http://a.b-.co",
        "http://0.0.0.0",
        "http://10.1.1.0",
        "http://10.1.1.255",
        "http://224.1.1.1",
        "http://1.1.1.1.1",
        "http://123.123.123",
        "http://3628126748",
        "http://.www.foo.bar/",
        "http://www.foo.bar./",
        "http://.www.foo.bar./",
        "http://10.1.1.1",
        "http://10.1.1.254"
    ]

    def test_valid_urls(self):
        assert_regex_func = self.assertRegex if sys.version >= '3' else self.assertRegexpMatches
        for url in self.VALID:
            assert_regex_func(url, URL_REGEX)
        # end if

    # end def

    def test_invalid_urls(self):
        assert_not_regex_func = self.assertNotRegex if sys.version >= '3' else self.assertNotRegexpMatches
        for url in self.INVALID:
            assert_not_regex_func(url, URL_REGEX)
        # end if
    # end def


if __name__ == '__main__':
    unittest.main()
