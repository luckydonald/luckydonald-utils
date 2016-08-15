# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging


from luckydonaldUtils.logger import logging
from pip.commands.install import InstallCommand
from pip.baseparser import ConfigOptionParser
from pip.exceptions import PipError
from pip.utils import get_prog

# Littlepip is best pony!

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)

install_cmd = InstallCommand()


def pip_install(*args):
    # # pip.create_main_parser()
    # pip.basecommand.Command.__init__
    args = args[:]
    parser_kw = {
        'usage': install_cmd.usage,
        'prog': '%s %s' % (get_prog(), install_cmd.name),
        'formatter': None,  # UpdatingDefaultsHelpFormatter(),
        'add_help_option': False,
        'name': install_cmd.name,
        'description': install_cmd.__doc__,
        'isolated': False,
    }
    parser = ConfigOptionParser(**parser_kw)
    options, parsed_args = parser.parse_args(args=args)
    try:
        status = install_cmd.run(options, parsed_args)
        if isinstance(status, int):
            logger.debug("Returned status code: {status}".format(status=status))
            return status == 0
    except (PipError, KeyboardInterrupt) as exc:
        logger.critical(str(exc))
        logger.debug('Exception information:', exc_info=True)
        return False
    except:
        logger.critical('Exception:', exc_info=True)
        return False
    return True
