# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

import getpass

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
eval_safe_builtin_list = ['math', 'acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh',
             'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot',
             'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians', 'sin',
             'sinh', 'sqrt', 'tan', 'tanh']


class NotAllowed(Exception):
    """
    Thrown when a command in NoBuiltins is not allowed.
    """
    pass
# end class


class NoBuiltins(object):
    def __init__(self, allowed_builtins, allowed_vars=None):
        """
        :param allowed_buildins: List with names of allowed buildins.
        :type  allowed_buildins: list[str]
        :param allowed_vars: Dict with allowed variables.
        :type  allowed_vars: dict

        """
        self.allowed_buildins = tuple(allowed_builtins)  # tuples are not modifiable.
        assert isinstance(allowed_vars, dict)
        self.var_store = allowed_vars
    # end def

    def __getitem__(self, item):
        if item in self.var_store:
            return self.var_store[item]
        if item in self.allowed_buildins:
            return __builtins__[item]
        raise NotAllowed(
            "{item} is not allowed, the supported commands are {allowed_funcs}, "
            "allowed variables are {allowed_vars}".format(
                item=item, allowed_funcs=self.allowed_buildins, allowed_vars=self.var_store.keys()
            ))
    # end def
# end class


def safe_eval(user_input, no_builtins_object=NoBuiltins(eval_safe_builtin_list)):
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
