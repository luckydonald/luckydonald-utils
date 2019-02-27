import unittest
from luckydonaldUtils.functions import caller, CallerResult
from luckydonaldUtils.logger import logging
logging.add_colored_handler(level=logging.DEBUG)


@caller(0)
def single_level_number(call):
    """
    TEst function replying the call arg unchanged
    :type  call: CallerResult
    :rtype: CallerResult
    """
    return call
# end def


@caller
def single_level_no_params(call):
    """
    TEst function replying the call arg unchanged
    :type  call: CallerResult
    :rtype: CallerResult
    """
    return call
# end def


@caller(kwarg_name='different_call')
def single_kwarg_params(different_call):
    """
    Test that we can provide a custom attribute.
    :type  different_call: CallerResult
    :rtype: CallerResult
    """
    return different_call
# end def


def duo_level_outer():
    """
    TesT function replying the call arg unchanged, one level in
    Outer/first level.
    :rtype: CallerResult
    """

    @caller(+1)
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
    def test_one_level_number(self):
        result = single_level_number()

        print(repr(result))
        self.assertIsNotNone(result['self'], 'single level: self.name (old access style)')
        self.assertEqual("single_level_number", result['self']['name'], 'single level: self.name (old access style)')

        self.assertIsNotNone(result['caller'], 'single level: caller.name (old access style)')
        self.assertEqual("test_one_level_number", result['caller']['name'], 'single level: caller.name (old access style)')
    # end def

    def test_one_level_new_number(self):
        result = single_level_number()
        self.assertIsInstance(result, CallerResult, 'caller result should be class CallerResult.')

        self.assertIsNotNone(result.self, 'single level: self.name (new access style)')
        self.assertEqual("single_level_number", result.self.name, 'single level: self.name (new access style)')

        self.assertIsNotNone(result.caller, 'single level: caller.name (new access style)')
        self.assertEqual("test_one_level_new_number", result.caller.name, 'single level: caller.name (new access style)')
    # end def

    def test_one_level_no_params(self):
        result = single_level_no_params()

        print(repr(result))
        self.assertIsNotNone(result['self'], 'single level: self.name (old access style)')
        self.assertEqual("single_level_no_params", result['self']['name'], 'single level: self.name (old access style)')

        self.assertIsNotNone(result['caller'], 'single level: caller.name (old access style)')
        self.assertEqual("test_one_level_no_params", result['caller']['name'], 'single level: caller.name (old access style)')
    # end def

    def test_one_level_new_no_params(self):
        result = single_level_no_params()
        self.assertIsInstance(result, CallerResult, 'caller result should be class CallerResult.')

        self.assertIsNotNone(result.self, 'single level: self.name (new access style)')
        self.assertEqual("single_level_no_params", result.self.name, 'single level: self.name (new access style)')

        self.assertIsNotNone(result.caller, 'single level: caller.name (new access style)')
        self.assertEqual("test_one_level_new_no_params", result.caller.name, 'single level: caller.name (new access style)')
    # end def

    def test_two_level(self):
        result = duo_level_outer()

        self.assertIsNotNone(result, 'duo level (old access style)')
        self.assertIsNotNone(result['self'], 'duo level: self.name (old access style)')
        self.assertEqual("duo_level_inner", result['self']['name'], 'duo level: self.name (old access style)')

        self.assertIsNotNone(result['caller'], 'duo level: caller.name (old access style)')
        self.assertEqual("test_two_level", result['caller']['name'], 'duo level: caller.name (old access style)')
    # end def

    def test_two_level_new(self):
        result = duo_level_outer()
        self.assertIsNotNone(result, 'single level (new access style)')
        self.assertIsInstance(result, CallerResult, 'caller result should be class CallerResult.')

        self.assertIsNotNone(result.self, 'single level: self.name (new access style)')
        self.assertEqual("duo_level_inner", result.self.name, 'single level: self.name (new access style)')

        self.assertIsNotNone(result.caller, 'single level: caller.name (new access style)')
        self.assertEqual("test_two_level_new", result.caller.name, 'single level: caller.name (new access style)')
    # end def

    def test_kwarg(self):
        result = single_kwarg_params()
        self.assertIsNotNone(result, 'single level (new access style)')
        self.assertIsInstance(result, CallerResult, 'caller result should be class CallerResult.')

        self.assertIsNotNone(result.self, 'single level: self.name (new access style)')
        self.assertEqual("single_kwarg_params", result.self.name, 'single level: self.name (new access style)')

        self.assertIsNotNone(result.caller, 'single level: caller.name (new access style)')
        self.assertEqual("test_kwarg", result.caller.name, 'single level: caller.name (new access style)')
    # end def

if __name__ == '__main__':
    unittest.main()
