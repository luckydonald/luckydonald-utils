# -*- coding: utf-8 -*-
from html import escape
from typing import Union

from pytgbot.api_types.receivable.peer import User
from pytgbot.exceptions import TgApiException
from pytgbot import Bot

from ....logger import logging


__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


def format_user(
    user: User, do_link: bool = False, prefer_username: bool = False, id_fallback: bool = False,
    user_tag: bool = None, id_tag: bool = None, html_escape: bool = True
) -> str:
    """
    Gets a user's name.

    If you want to use it in html you should probably keep html character escaping enabled (`html_escape=True`).
    You can specify to wrap the user name string or id string in html tags, with the user_tag or id_tag arguments.
    If the name is "Max Mustermann", with `user_tag="b"` it will return "<b>Max Mustermann</b>".

    Could return `None` if that user was either not found, or had no usable data.

    :param user: the telegram user object.
    :param do_link: If it should do a link instead of bold or anything provided in `user_tag` or `id_tag`.
    :param prefer_username: if you should prefer the @username over the real name
    :param id_fallback: if no real name and no @username exists, if it should fallback to the user id: user#123456
    :param user_tag: Name of the html tag to wrap the user string in (not the @username)
    :param id_tag: Name of the html tag to wrap the user id in. (`id_fallback` must be `True`)
    :param html_escape: If html tags in strings should be escaped. Default: True

    :return: the (formatted) name
    """
    assert isinstance(user, User)

    def maybe_escape(text):
        """
        None >-------------------------> None
        text >-- html_escape = True ---> escape(text)
        text >-- html_escape = False --> text
        """
        return escape(text) if (text is not None and html_escape) else text
    # end def

    name = None
    if user.first_name:
        if user.last_name:  # first + last
            name = maybe_escape(user.first_name + " " + user.last_name)
        else:  # only first
            name = maybe_escape(user.first_name)
        # end if
        if do_link:
            name = '<a href="tg://user?id={id}">{name}</a>'.format(id=user.id, name=name)
        elif user_tag:
            name = "<{tag}>{name}</{tag}>".format(tag=user_tag, name=name)
        # end if
    else:
        if user.last_name:  # only last
            name = maybe_escape(user.last_name)
            if do_link:
                name = '<a href="tg://user?id={id}">{name}</a>'.format(id=user.id, name=name)
            elif user_tag:
                name = "<{tag}>{name}</{tag}>".format(tag=user_tag, name=name)
            # end if
        # end if
    # end if

    # fallback if no fist/lastname or overwrite if prefer_username.
    if user.username and (name is None or prefer_username):
        name = "@" + maybe_escape(user.username)
    # end if

    # id fallback
    if not name and user.id and id_fallback:
        name = maybe_escape("user#" + str(user.id))
        if do_link:
            name = '<a href="tg://user?id={id}">{name}</a>'.format(id=user.id, name=name)
        elif id_tag:
            name = "<{tag}>{name}</{tag}>".format(tag=id_tag, name=name)
        # end if
    # end if
    return name
# end def


def retrieve_and_format_user(
    bot: Bot, user_id: Union[str, int], do_link: bool = False, prefer_username: bool = False, id_fallback: bool = False,
    user_tag: bool = None, id_tag: bool = None, html_escape: bool = True
) -> str:
    """
    Gets a user's name by given user id.

    If you want to use it in html you should probably keep html character escaping enabled (`html_escape=True`).
    You can specify to wrap the user name string or id string in html tags, with the user_tag or id_tag arguments.
    If the name is "Max Mustermann", with `user_tag="b"` it will return "<b>Max Mustermann</b>".

    Could return `None` if that user was either not found, or had no usable data.

    :param bot: The bot instance to use to check the user.
    :param user_id: the id of the telegram user.
    :param do_link: If it should do a link instead of bold or anything provided in `user_tag` or `id_tag`.
    :param prefer_username: if you should prefer the @username over the real name
    :param id_fallback: if no real name and no @username exists, if it should fallback to the user id: user#123456
    :param user_tag: Name of the html tag to wrap the user string in (not the @username)
    :param id_tag: Name of the html tag to wrap the user id in. (`id_fallback` must be `True`)
    :param html_escape: If html tags in strings should be escaped. Default: True

    :return: the (formatted) name
    """
    try:
        user = bot.get_chat_member(user_id, user_id).user
    except TgApiException:
        if id_fallback:
            name = "user#" + str(user_id)
            name = escape(name) if (name is not None and html_escape) else name
            if do_link:
                return '<a href="tg://user?id={id}">{name}</a>'.format(id=user_id, name=name)
            if id_tag:
                return "<{tag}>{name}</{tag}>".format(tag=id_tag, name=name)
            # end if
        # end if
        return None
    # end try
    return format_user(
        user,
        do_link=do_link, prefer_username=prefer_username, id_fallback=id_fallback,
        user_tag=user_tag, id_tag=id_tag, html_escape=html_escape
    )
# end def
