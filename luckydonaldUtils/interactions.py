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
		if default == True:
			prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
		else:
			prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')
	else:
		prompt += ' y|n: ' # "%s y|n"
	#end if
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
	#end while
#end def


def answer(prompt=None, default=None):
	if prompt is None:
		prompt = 'Input'
	#end if
	if default is not None:
		prompt = '{prompt} [{default}]: '.format(prompt=prompt, default=default)
	else:
		prompt = '{prompt}: '.format(prompt=prompt)
	ans = None
	while not ans:
		ans = input(prompt)
		if not ans and default is not None:
			return default
		#end if
	#end while, when the user finally entered something
	return ans
#end def


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