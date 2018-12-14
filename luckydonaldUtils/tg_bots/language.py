from typing import Type, Dict, TypeVar, cast, Union, Optional, Callable

from ..exceptions import assert_type_or_raise
from ..dependencies import import_or_install

try:
    from pytgbot.api_types.receivable.updates import Update, Message
except ImportError:  # pragma nocover
    Update = import_or_install("pytgbot.api_types.receivable.updates", "Update")  # pip install pytgbot
    Message = import_or_install("pytgbot.api_types.receivable.updates", "Message")  # pip install pytgbot


# end try


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
    return update_msg_or_language_code


# end def


T = TypeVar('T')


def create_l(DefaultLang: Type[T], LANG: Dict[str, T]) -> Callable:
    """
    Creates a new l function.
    :param DefaultLang:
    :param LANG:
    :return:
    """

    def l(update_msg_or_language_code: Union[Update, Message, str, None] = None) -> DefaultLang:
        lang = get_language_code(update_msg_or_language_code)

        # if it now is None (default, or getting from message failed), use the default
        if lang is None or lang not in LANG:
            return cast(DefaultLang, LANG['default'])
        # end if
        return cast(DefaultLang, LANG[lang])

    # end def
    return l
# end def
