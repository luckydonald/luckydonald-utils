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


STATUS_IS_GONE = ("left", "kicked")


def is_member(chat_member: ChatMember) -> bool:
    """
    Checks if a user is still in a chat.

    :param chat_member: The ChatMember object to decide upon.

    :return:
    """
    if chat_member.status in STATUS_IS_GONE:
        return False
    # end if
    return True
# end def


def retrieve_and_is_member(bot: Bot, chat_id: int, user_id: int) -> bool:
    """
    Checks if a user is still in a chat/group.
    If lookup fails, `False` is assumed.

    :param bot: The bot to execute the get_chat_member request with.
    :param chat_id: id of the chat the user should be in
    :param user_id: id of the user

    :return:
    """
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        logger.debug(f'get_chat_member result: {chat_member}')
        return is_member(chat_member)
    except TgApiException:
        logger.exception('calling get_chat_member failed. Defaulting to \'no admin\'.')
        return False
    # end try
# end def
