from typing import Type, Dict, TypeVar, cast, Union, Optional, Callable

from ..exceptions import assert_type_or_raise
from ..dependencies import import_or_install

try:
    from pytgbot.api_types.receivable.updates import Update, Message
except ImportError:  # pragma nocover
    Update = import_or_install("pytgbot.api_types.receivable.updates", "Update")  # pip install pytgbot
    Message = import_or_install("pytgbot.api_types.receivable.updates", "Message")  # pip install pytgbot
# end try

__all__ = ['get_language_code', 'l_get']

LangClass = TypeVar('LangClass')


def get_language_code(update_msg_or_language_code: Union[Update, Message, str, None] = None) -> Optional[str]:
    assert_type_or_raise(update_msg_or_language_code, None, str, Message, Update, parameter_name="msg")

    # if is message, get the language_code from there.
    if isinstance(update_msg_or_language_code, Update) and update_msg_or_language_code.message:
        # we are in a update, we want the message
        update_msg_or_language_code = update_msg_or_language_code.message
    # end if
    if isinstance(update_msg_or_language_code, Message):
        # we are in a message, we want the language_code
        if not update_msg_or_language_code.from_peer or not update_msg_or_language_code.from_peer.language_code:
            return None
        else:
            return update_msg_or_language_code.from_peer.language_code
        # end if
    # end if
    if not isinstance(update_msg_or_language_code, str):
        return None
    # end if
    return update_msg_or_language_code
# end def


def l_get(
        language_dict: Dict[str, LangClass], update_msg_or_language_code: Union[Update, Message, str, None] = None
) -> LangClass:
    """
    Retrieves a translation string for a given update/message/language_code.

    :param language_dict: the array containing the languages.
    :param update_msg_or_language_code: The stuff containing language info.
    :return: the fitting language class.
    """
    lang = get_language_code(update_msg_or_language_code)

    # if it is None (default, or getting from message failed), use the default
    if lang is None:
        return language_dict['default']
    # end if

    if lang in language_dict:
        return language_dict[lang]
    # end if

    # try splitting it "de_DE" => "de"
    part = lang.split('-')[0]
    if part in language_dict:
        return language_dict[part]
    # end of

    # try splitting it "de-DE" => "de"
    part = lang.split('_')[0]
    if part in language_dict:
        return language_dict[part]
    # end if

    # nothing did match, use the default
    return language_dict['default']
# end def
