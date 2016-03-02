# -*- coding: utf-8 -*-
import getpass
import math

__author__ = 'luckydonald'

try:
    input = raw_input
except NameError:
    input = input
raw_input = input


# modified from http://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/
def confirm(prompt=None, default=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', default=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', default=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', default=False)
    Create Directory? [n]|y: y
    True

    """

    if prompt is None:
        prompt = 'Confirm'

    if default is not None:
        if default:
            prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
        else:
            prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')
    else:
        prompt += ' y|n: '  # "%s y|n"
    # end if
    while True:
        ans = input(prompt)
        if not ans and default is not None:
            return default
        if ans not in ['y', 'Y', 'n', 'N']:
            print('Please enter y or n.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False
        # end if
    # end while
# end def


def answer(prompt=None, default=None):
    if prompt is None:
        prompt = 'Input'
    # end if
    if default is not None:
        prompt = '{prompt} [{default}]: '.format(prompt=prompt, default=default)
    else:
        prompt = '{prompt}: '.format(prompt=prompt)
    ans = None
    while not ans:
        ans = input(prompt)
        if not ans and default is not None:
            return default
            # end if
    # end while, when the user finally entered something
    return ans
# end def


def password(prompt=None, default=None):
    """
    If default is None, it will retry until the user inputs something.
    else set default="" to allow empty inputs.

    :param prompt: defaults to "Password"
    :param default:
    :return:
    """
    if prompt is None:
        prompt = 'Password'
    if default is not None:
        prompt = '{prompt} [{default}]: '.format(prompt=prompt, default=default)
    else:
        prompt = '{prompt}: '.format(prompt=prompt)
    passw = None
    while not passw:
        passw = getpass.getpass(prompt=prompt)
        if not passw and default is not None:
            return default
        # end if
    # end while
# end def




################################################
#                                              #
# SAFE EVAL    (could have holes in it...)     #
#                                              #
# modified from                                #
# http://lybniz2.sourceforge.net/safeeval.html #
#                                              #
################################################

# make a list of safe functions
eval_safe_builtin_list = ["math"]
eval_safe_builtin_mapping = {'acos': math.acos, 'asin': math.asin, 'atan': math.atan,
                                  'atan2': math.atan2, 'ceil': math.ceil, 'cos': math.cos, 'cosh': math.cosh,
                                  'degrees': math.degrees, 'e': math.e, 'exp': math.exp, 'fabs': math.fabs,
                                  'floor': math.floor, 'fmod': math.fmod, 'frexp': math.frexp, 'hypot': math.hypot,
                                  'ldexp': math.ldexp, 'log': math.log, 'log10': math.log10, 'modf': math.modf,
                                  'pi': math.pi, 'pow': math.pow, 'radians': math.radians, 'sin': math.sin,
                                  'sinh': math.sinh, 'sqrt': math.sqrt, 'tan': math.tan, 'tanh': math.tanh
}


class NotAllowed(Exception):
    """
    Thrown when a command in NoBuiltins is not allowed.
    """
    pass
# end class


class NoBuiltins(object):
    def __init__(self, allowed_builtins, allowed_functions=None, allowed_vars=None):
        """
        :param allowed_builtins: List with names of functions.
        :type  allowed_builtins: list[str]
        :param allowed_functions: Dict with names of functions and the functions to be called.
        :type  allowed_functions: dict
        :param allowed_vars: Dict with allowed variables.
        :type  allowed_vars: dict

        """
        assert isinstance(allowed_builtins, list)
        self.allowed_builtins = tuple(allowed_builtins)  # tuples are not modifiable.
        if allowed_functions is None:
            allowed_functions = {}
        assert isinstance(allowed_functions, dict)
        self.allowed_functions = allowed_functions
        if allowed_vars is None:
            allowed_vars = {}
        assert isinstance(allowed_vars, dict)
        self.var_store = allowed_vars
    # end def

    def __getitem__(self, item):
        if item in self.var_store:
            return self.var_store[item]
        if item in self.allowed_functions:
            return self.allowed_functions[item]
        if item in self.allowed_builtins:
            return __builtins__[item]
        all = list(self.var_store.keys())
        all.extend(self.allowed_functions)
        raise NotAllowed(
            "{item} is not allowed, the supported commands are {allowed_funcs}, "
            "allowed variables are {allowed_vars}.".format(
                item=item, allowed_funcs=all, allowed_vars=self.var_store.keys()
            ))
    # end def
# end class


def safe_eval(user_input, no_builtins_object=NoBuiltins(eval_safe_builtin_list, eval_safe_builtin_mapping)):
    """
    Evals the `user_input` string.

    The NoBuiltins raises a `NotAllowed` Exception when the command is not allowed.
    :param user_input:
    :param no_builtins_object:
    :param question:
    :return:
    """
    assert isinstance(user_input, str)
    assert isinstance(no_builtins_object, NoBuiltins)
    result = eval(user_input, {"__builtins__": no_builtins_object}, no_builtins_object)
    return result


"""
>>> safe_eval("log10(12)")
1.0791812460476249
"""