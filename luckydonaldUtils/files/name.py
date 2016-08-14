# -*- coding: utf-8 -*-
from luckydonaldUtils.files import logger
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'
logger = logging.getLogger(__name__)


def do_a_filename(input_file_name):
    """
    This is a bad try to make file names better, replacing various characters with best fitting ascii ones.
    This does only include a basic set of replacements.
    Note: In no way the output should be considered safe to use! Not all non-ascii characters are replaced!
    """
    output_file_name = input_file_name
    for replacer in [(":", ""), ("?", ""), ("*", ""), ("”", "\""), (">", ""), ("<", ""), ("|", "-"), ("\\", " "),
                     ("/", " ")]:
        output_file_name = output_file_name.replace(replacer[0], replacer[1])
    logger.debug("Filename '{old_filename}' is now '{new_filename}'.".format(old_filename=input_file_name,
                                                                             new_filename=output_file_name))
    return output_file_name
