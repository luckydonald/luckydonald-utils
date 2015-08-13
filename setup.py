# -*- coding: utf-8 -*-
__author__ = 'luckydonald'

from setuptools import setup

long_description = """A collection of utilities I use across different projects"""

setup(
	name="luckydonald's utilities",
	version="0.1",
	author="luckydonald",
	author_email="code@luckydonald.de",
	description=long_description,
	license="BSD",
	keywords="example documentation tutorial",
	url="https://github.com/luckydonald/python-utils",
	packages=['luckydonaldUtils'],
	install_requires=["pip", "importlib"],
	long_description=long_description,
	classifiers=[
		"Development Status :: 4 - Beta",
		"Intended Audience :: Developers",
		"Topic :: Utilities",
		"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
	],
)
