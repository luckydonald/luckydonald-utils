# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

from setuptools import setup
from luckydonaldUtils import VERSION
from luckydonaldUtils.dependencies import find_submodules


long_description = """A collection of utilities I use across different projects"""

# http://peterdowns.com/posts/first-time-with-pypi.html
# $ python setup.py register -r pypi
# $ python setup.py sdist upload -r pypi

main_package = 'luckydonaldUtils'

install_requires = ["pip", "setuptools"]  # both should be installed by default.
try:
	import importlib
except ImportError:
	install_requires.append('importlib')

setup(
	name="luckydonald-utils",
	packages=find_submodules(main_package),
	version=VERSION,
	author="luckydonald",
	author_email="code@luckydonald.de",
	description=long_description,
	license="BSD",
	keywords="example documentation tutorial",
	url="https://github.com/luckydonald/python-utils",
	install_requires=install_requires,
	long_description=long_description,
	classifiers=[
		"Development Status :: 4 - Beta",
		"Intended Audience :: Developers",
		"Topic :: Utilities",
		"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
	],
)
