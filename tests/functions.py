import unittest
from luckydonaldUtils.functions import caller, CallerResult
from luckydonaldUtils.logger import logging
logging.add_colored_handler(level=logging.DEBUG)


@caller
def single_level(call):
    """
    TEst function replying the call arg unchanged
    :type  call: CallerResult
    :rtype: CallerResult
    """
    return call
# end def


def duo_level_outer(wanna_get_inner=True):
    """
    TesT function replying the call arg unchanged, one level in
    Outer/first level.
    :rtype: CallerResult
    """

    @caller(1)
    def duo_level_inner(call):
        """
        TeSt function replying the call arg unchanged, the second level in
        :type  call: CallerResult
        :rtype: CallerResult
        """
        return call
    # end def

    return duo_level_inner()
# end def


class CallerTestCase(unittest.TestCase):
    def test_one_level(self):
        result = single_level()

        self.assertIsNotNone(result['self'], 'single level: self.name (old access style)')
        self.assertEqual("single_level", result['self']['name'], 'single level: self.name (old access style)')

        self.assertIsNotNone(result['caller'], 'single level: caller.name (old access style)')
        self.assertEqual("test_one_level", result['caller']['name'], 'single level: caller.name (old access style)')
    # end def

    def test_one_level_new(self):
        result = single_level()
        self.assertIsInstance(result, CallerResult, 'caller result should be class CallerResult.')

        self.assertIsNotNone(result.self, 'single level: self.name (new access style)')
        self.assertEqual("single_level", result.self.name, 'single level: self.name (new access style)')

        self.assertIsNotNone(result.caller, 'single level: caller.name (new access style)')
        self.assertEqual("test_one_level_new", result.caller.name, 'single level: caller.name (new access style)')
    # end def

    def test_two_level(self):
        result = duo_level_outer(False)

        self.assertIsNotNone(result, 'duo level (old access style)')
        self.assertIsNotNone(result['self'], 'duo level: self.name (old access style)')
        self.assertEqual("duo_level_outer", result['self']['name'], 'duo level: self.name (old access style)')

        self.assertIsNotNone(result['caller'], 'duo level: caller.name (old access style)')
        self.assertEqual("test_two_level", result['caller']['name'], 'duo level: caller.name (old access style)')
    # end def

    def test_two_level_new(self):
        result = duo_level_outer(True)
        self.assertIsNotNone(result, 'single level (new access style)')
        self.assertIsInstance(result, CallerResult, 'caller result should be class CallerResult.')

        self.assertIsNotNone(result.self, 'single level: self.name (new access style)')
        self.assertEqual("duo_level_outer", result.self.name, 'single level: self.name (new access style)')

        self.assertIsNotNone(result.caller, 'single level: caller.name (new access style)')
        self.assertEqual("test_two_level_new", result.caller.name, 'single level: caller.name (new access style)')
    # end def

if __name__ == '__main__':
    unittest.main()
