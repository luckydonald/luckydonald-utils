
import logging
from setuptools import find_packages

logger = logging.getLogger(__name__)

import pip
try:
	import importlib
except ImportError:
	# pip install importlib
	pip.main(["install", "importlib"])
	import importlib
#end try


def import_or_install(package_name, pip_name=None):
	"""
	Trys to import an package.
	If that fails it tries to install it via pip, using the given `pip_name` or if not given, the `package_name`.
	:param package_name:  Package name to import. (E.g. "PIL")
	:param pip_name:  The name to install it like `$pip install <pip_name>` would do. (E.g. "Pillow")
	:return:
	"""
	if pip_name is None:
		pip_name = package_name
	# pytz.timzone -> from pytz import timezone -> package_name = pytz, from_package = [timezone]
	imp = None
	for try_i in [1,2,3]:
		try:
			err = None
			imp = import_only(package_name)
			break
		except ImportError as e:
			err = e
			logger.debug("Import failed.", exc_info=True)
			upgrade = try_i >= 2  # import failed twice (one after doing a normal install)
			install_only(pip_name, upgrade)
	else:
		raise err
	return imp

def import_only(package_name, module_list=None):
	if not module_list:
		if "." in package_name:
			package_name, module_list = package_name.rsplit('.', 1)
		else:
			module_list = None
	if module_list:
		logger.debug("Trying import: form \"{module_name}\" import \"{module_list}\".".format(module_name=package_name, module_list=module_list))
	else:
		logger.debug("Trying to import module \"{module_name}\".".format(module_name=package_name))

	try:
		imp = importlib.import_module(package_name)
		if module_list:
			if hasattr(imp, module_list):
				imp = getattr(imp, module_list)
				logger.debug("\"{module_list}\" is an attribute of \"{module_name}\".".format(module_name=package_name, module_list=module_list))
			else:
				imp = importlib.import_module(package_name, package=module_list)
				logger.debug("\"{module_list}\" is an module in \"{module_name}\".".format(module_name=package_name, module_list=module_list))
		else:
			imp = importlib.import_module(package_name, package=module_list)
			logger.debug("module \"{module_name}\".".format(module_name=package_name))

	except ImportError:
		imp = importlib.import_module(package_name, package=module_list)
	return imp


def install_only(pip_name, upgrade=False):
	logger.warn("{install_or_upgrade} package '{pip_name}'.\n"
		   "If that fails, install it manually:\n"
		   "pip install {pip_name}\n"
		   "".format(pip_name=pip_name, install_or_upgrade="Upgrading" if upgrade else "Installing"))
	args = ["install", pip_name, "--verbose"]
	if upgrade and not "--upgrade" in args:
		args.append("--upgrade")
	logger.debug("Trying to install \"{pip_name}\" with pip using the following arguments: {pip_args}...".format(pip_name=pip_name, pip_args=args))
	return pip.main(args)

def upgrade(pip_name):
	install_only(pip_name, upgrade=True)


def find_submodules(main_package):
	packages = [main_package]
	for package in find_packages(where=main_package):
		packages.append(main_package + "." + package)
	return packages