# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging

try:
    from .pip_interface import pip_install
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warn("Could not apply logger workaround. Falling back to using pip directly.")
    from .pip_interface_fallback import pip_install
# end try

from setuptools import find_packages

try:
    import importlib
except ImportError:
    # pip install importlib
    pip_install(["importlib"])
    import importlib
# end try

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


def import_or_install(package_name, pip_name=None):
    """
    Tries to import an package.
    If that fails it tries to install it via pip, using the given `pip_name` or if not given, the `package_name`.
    :param package_name:  Package name to import. (E.g. "PIL")
    :param pip_name:  The name to install it like `$pip install <pip_name>` would do. (E.g. "Pillow")
    :return:
    """
    # if pip name is given, just use that.
    if pip_name:
        return import_or_install_with_exact_pip_name(package_name, pip_name)
    # if pip name is not given, try posibilities, by splitting the dots.
    #
    # Example:
    #  >> import_or_install("imgurpython.client.ImgurClient")
    # will try to install:
    #   - "imgurpython"
    #   - "imgurpython.client"
    #   - "imgurpython.client.ImgurClient"
    #
    # This also allows package names containing dots like "ruamel.yaml".
    pip_name = ""
    err = None
    for part in package_name.split("."):
        pip_name = (pip_name + "." if pip_name else "") + part
        try:
            return import_or_install_with_exact_pip_name(package_name, pip_name)
        except ImportError as e:
            err = e
            logger.debug("Import failed.", exc_info=True)
            # end try
    # end for
    raise err  # should store the last occurred error.


# end def


def import_or_install_with_exact_pip_name(package_name, pip_name):
    """
    Just a helper for import_or_install()

    Also Littlepip is best pony.
    """
    err = None
    for try_i in [1, 2, 3]:
        try:
            return import_only(package_name)
        except ImportError as e:
            err = e
            logger.debug("Import failed.", exc_info=True)
            upgrade = try_i >= 2  # import failed twice (one after doing a normal install)
            install_only(pip_name, upgrade)
    raise err  # should store the last occurred error.


# end def


def import_only(package_name, module_list=None):
    # "pytz.timzone" -> from pytz import timezone -> package_name = "pytz", from_package = ["timezone"]
    if not module_list:
        if "." in package_name:
            package_name, module_list = package_name.rsplit('.', 1)
        else:
            module_list = None
    if module_list:
        logger.debug("Trying import: form \"{module_name}\" import \"{module_list}\".".format(module_name=package_name,
                                                                                              module_list=module_list))
    else:
        logger.debug("Trying to import module \"{module_name}\".".format(module_name=package_name))

    try:
        imp = importlib.import_module(package_name)
        if module_list:
            if hasattr(imp, module_list):
                imp = getattr(imp, module_list)
                logger.debug("\"{module_list}\" is an attribute of \"{module_name}\".".format(module_name=package_name,
                                                                                              module_list=module_list))
            else:
                imp = importlib.import_module(package_name, package=module_list)
                logger.debug("\"{module_list}\" is an module in \"{module_name}\".".format(module_name=package_name,
                                                                                           module_list=module_list))
        else:
            imp = importlib.import_module(package_name, package=module_list)
            logger.debug("module \"{module_name}\".".format(module_name=package_name))

    except ImportError:
        try:
            imp = importlib.import_module(package_name, package=module_list)
        except (SystemError, ValueError) as e:
            # https://github.com/luckydonald/luckydonald-utils/issues/2
            # https://bugs.python.org/issue18018
            raise ImportError(str(e))
    return imp


def install_only(pip_name, upgrade=False):
    logger.warn("{install_or_upgrade} package '{pip_name}'.\n"
                "If that fails, install it manually:\n"
                "pip install {pip_name}\n"
                "".format(pip_name=pip_name, install_or_upgrade="Upgrading" if upgrade else "Installing"))
    args = [pip_name, "--verbose"]
    if upgrade and "--upgrade" not in args:
        args.append("--upgrade")
    logger.debug("Trying to install \"{pip_name}\" with pip using the following arguments: {pip_args}...".format(
        pip_name=pip_name, pip_args=args))
    return pip_install(args)


def upgrade(pip_name):
    install_only(pip_name, upgrade=True)


def find_submodules(main_package):
    packages = [main_package]
    for package in find_packages(where=main_package):
        packages.append(main_package + "." + package)
    return packages
