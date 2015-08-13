
import logging
logger = logging.getLogger(__name__)

import pip
try:
	import importlib
except ImportError:
	# pip install importlib
	pip.main(["install", "importlib"])
	import importlib
#end try


def import_or_install(package_name, pip_name):
	# pytz.timzone -> from pytz import timezone -> package_name = pytz, from_package = [timezone]
	if "." in package_name:
		package_name, module_list = package_name.rsplit('.', 1)
	else:
		module_list = None
	imp = None
	for try_i in [1,2,3]:
		try:
			err = None
			imp = import_only(package_name, module_list=module_list)
			break
		except ImportError as e:
			err = e
			logger.debug("Import failed.")
			upgrade = try_i >= 2  # import failed twice (one after doing a normal install)
			install_only(pip_name, upgrade)
	else:
		raise err
	return imp

def import_only(package_name, module_list=None):
	if module_list:
		logger.debug("Trying import: form \"{module_name}\" import \"{module_list}\".".format(module_name=package_name, module_list=module_list))
	else:
		logger.debug("Trying to import module \"{module_name}\".".format(module_name=package_name))
	return importlib.import_module(package_name, package=module_list)


def install_only(pip_name, upgrade=False):
	logger.warn("Installing package '{pip_name}'.\n"
		   "If that fails, install it manually:\n"
		   "pip install {pip_name}\n"
		   "".format(pip_name=pip_name))
	args = ["install", pip_name, "--quiet"]
	if upgrade:
		args.append("--upgrade")
	logger.debug("Trying to install \"{pip_name}\" with pip using the following arguments: {pip_args}".format(pip_name=pip_name, pip_args=args))
	return pip.main(args)