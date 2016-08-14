# -*- coding: utf-8 -*-
from setuptools import setup
from luckydonaldUtils import VERSION
from luckydonaldUtils.dependencies import find_submodules

__author__ = 'luckydonald'
long_description = """A collection of utilities I use across different projects"""

# http://peterdowns.com/posts/first-time-with-pypi.html
# $ python setup.py register -r pypi
# $ python setup.py sdist upload -r pypi

main_package = 'luckydonaldUtils'

install_requires = ["pip", "setuptools", "DictObject"]  # both should be installed by default.
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
    license="GPLv2+",
    keywords="luckydonald utils utilities utility python dependencies dependency download progress bar encoding files "
             "interactions json update store text xml time network logger color images webserver django CSRF headers "
             "eastereggs decorator holder assert raise is None",
    url="https://github.com/luckydonald/luckydonald-utils",
    install_requires=install_requires,
    long_description=long_description,
    # test_suite = 'nose.collector',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    ],
)
