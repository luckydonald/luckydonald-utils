# -*- coding: utf-8 -*-
from html import escape

from pytgbot.api_types.receivable.peer import Chat
from ...logger import logging


__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


def format_chat(chat: Chat):
    """
    Formats a channel for html, escaping username and title.
    Will try to link to the ID if possible.

    :param chat:
    :return:
    """
    escaped_title = escape(chat.title) if chat.title is not None else None           # this is used about everywhere
    escaped_username = escape(chat.username) if chat.username is not None else None  # this is used about everywhere
    logger.debug(f'creating representation of {chat!r}')
    if 'link' in chat and chat.invite_link:
        channel_link = f"<a href={chat.invite_link!r}>{escaped_title}</a>"
    elif 'username' in chat and chat.username:
        channel_link = f"<a href=\"https://t.me/{escaped_username}\">{escaped_title}</a>"
    else:
        channel_link = f"<b>{escaped_title}</b>"
    # end if
    if 'id' in chat and chat.id:
        if 'username' in chat and chat.username:
            channel_link += f" (<code>{chat.id}</code>, @{escaped_username})"
        else:
            channel_link += f" (<code>{chat.id}</code>)"
        # end if
    else:  # id not in data
        if 'username' in chat and chat.username:
            channel_link += f" (@{escaped_username})"
        else:
            pass
            # channel_link += f" (<i>???</i>)"
        # end if
    # end if

    return channel_link
# end def
