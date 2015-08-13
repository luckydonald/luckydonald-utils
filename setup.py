# -*- coding: utf-8 -*-
from luckydonaldUtils import VERSION

__author__ = 'luckydonald'

from setuptools import setup

long_description = """A collection of utilities I use across different projects"""

# http://peterdowns.com/posts/first-time-with-pypi.html
# $ python setup.py register -r pypi
# $ python setup.py sdist upload -r pypi

setup(
	name="luckydonald-utils",
	packages=['luckydonaldUtils'],
	version=VERSION,
	author="luckydonald",
	author_email="code@luckydonald.de",
	description=long_description,
	license="BSD",
	keywords="example documentation tutorial",
	url="https://github.com/luckydonald/python-utils",
	install_requires=["pip", "importlib"],
	long_description=long_description,
	classifiers=[
		"Development Status :: 4 - Beta",
		"Intended Audience :: Developers",
		"Topic :: Utilities",
		"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
	],
)
