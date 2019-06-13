# -*- coding: utf-8 -*-
from typing import Union

from ....dependencies import import_or_install

try:
    from pytgbot import Bot
    from pytgbot.api_types.receivable.peer import ChatMember
    from pytgbot.exceptions import TgApiException
except ImportError:  # pragma nocover
    Bot = import_or_install("pytgbot.bot", "Bot")  # pip install pytgbot
    ChatMember = import_or_install("pytgbot.api_types.receivable.peer", "ChatMember")  # pip install pytgbot
    TgApiException = import_or_install("pytgbot.exceptions", "TgApiException")  # pip install pytgbot
# end try


from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


STATUS_IS_ADMIN = ("creator", "administrator")


def is_admin(chat_member: ChatMember, right: Union[None, str] = None):
    """
    Checks if a user is admin (or even creator) of a chat/group. Optionally a specific right can be requested to exist.

    :param chat_member: The ChatMember object to decide upon.
    :param right: Right to require, e.g. `"can_promote_members"`.

    :return:
    """
    if chat_member.status not in STATUS_IS_ADMIN:
        return False  # needs to be admin
    # end if
    if right:  # so we wanna know if he has the right permissions.
        assert hasattr(chat_member, right)  # so the field exists.
        logger.debug('getattr(chat_member, right)' + repr(getattr(chat_member, right)) + ": " + repr(getattr(chat_member, right) == True))
        return getattr(chat_member, right) is True  # get value
    # end if
    return True
# end def


def retrieve_and_is_admin(bot: Bot, chat_id: int, user_id: int, right: Union[None, str] = None):
    """
    Checks if a user is admin (or even creator) of a chat/group. Optionally a specific right can be requested to exist.
    If lookup fails, `False` is assumed.

    :param bot: The bot to execute the get_chat_member request with.
    :param chat_id:
    :param user_id:
    :param right: Right to require, e.g. `"can_promote_members"`.

    :return:
    """
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        logger.debug(f'get_chat_member result: {chat_member}')
        return is_admin(chat_member, right=right)
    except TgApiException:
        logger.exception('calling get_chat_member failed. Defaulting to \'no admin\'.')
        return False
    # end try
# end def
