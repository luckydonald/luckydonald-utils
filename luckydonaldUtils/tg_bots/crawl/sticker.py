#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict

import requests

from luckydonaldUtils.logger import logging

from pytgbot.api_types.receivable.media import Sticker
from pytgbot.api_types.receivable.updates import Message, Update

from teleflask import TBlueprint

from ...regex.urls.telegram import ADDSTICKERS_REGEX

__author__ = 'luckydonald'


logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

GETSTICKERS_API_KEY = os.getenv('GETSTICKERS_API_KEY', None)
GETSTICKERS_API_URL = os.getenv('GETSTICKERS_API_URL', 'https://api.getstickers.me/v1')   # so we can switch to staging there.
GETSTICKERS_ENABLED = GETSTICKERS_API_KEY and GETSTICKERS_API_URL

TIMEOUT = 0.5


# noinspection PyCompatibility
class BotMessage(object):
    bot_id: int
    message: Message

    def __init__(self, bot_id, message):
        self.bot_id = bot_id
        self.message = message
    # end def

    def to_array(self):
        return {"bot_id": self.bot_id, "message": self.message.to_array()}
    # end def

    def __repr__(self):
        return f'{self.__class__.__name__}(bot_id={self.bot_id!r}, message={self.message!r})'
    # end def
# end class


# noinspection PyCompatibility
class CacheData(object):
    enabled: bool
    next_send: datetime
    queue: List[BotMessage]

    def __init__(self, queue=None, *, next_send=None, enabled=True):
        if queue is None:
            queue = []
        # end if
        if next_send is None:
            next_send = datetime.now() + SEND_INTERVAL
        # end if
        self.enabled = enabled
        self.queue = queue
        self.next_send = next_send
    # end def

    def __repr__(self):
        return f'{self.__class__.__name__}(enabled={self.enabled!r}, queue={self.queue!r}, next_send={self.next_send!r})'
    # end def
# end class



SEND_INTERVAL = timedelta(minutes=1)

# noinspection PyCompatibility
SEND_CACHE_STICKER = CacheData(enabled=True)

sticker_crawl_tbp = TBlueprint(__name__)

if not GETSTICKERS_ENABLED:
    logger.warning('Did not register sticker crawler as GETSTICKERS_API_KEY is not defined.')
    raise ImportError('Did not register sticker crawler as GETSTICKERS_API_KEY is not defined.')
# end if


@sticker_crawl_tbp.on_message
def on_sticker_message(update: Update, msg: Message):
    submit_sticker_message(msg)
    collect_pack_text(msg)
    return
# end def


@sticker_crawl_tbp.on_update('channel_post')
def on_sticker_update_channel_post(update: Update):
    submit_sticker_message(update.channel_post)
    collect_pack_text(update.channel_post)
    return
# end def


@sticker_crawl_tbp.on_update('edited_message')
def on_sticker_update_edited_message(update: Update):
    submit_sticker_message(update.edited_message)
    collect_pack_text(update.edited_message)
    return
# end def


@sticker_crawl_tbp.on_update('edited_channel_post')
def on_sticker_update_edited_channel_post(update: Update):
    submit_sticker_message(update.edited_channel_post)
    collect_pack_text(update.edited_channel_post)
    return
# end def


def collect_pack_text(message: Message):
    if not message.text or '/addstickers/' not in message.text:
        return
    # end if
    for match in ADDSTICKERS_REGEX.finditer(message.text):
        submit_pack(match.group('pack'))
    # end for
# end def


def submit_pack(pack_url: str):
    try:
        requests.put(
            GETSTICKERS_API_URL + '/submit/pack',
            params={
                "key": GETSTICKERS_API_KEY,
                "bot_id": sticker_crawl_tbp.user_id,
                "pack": pack_url,
            },
            timeout=TIMEOUT,
        )
    except requests.HTTPError as e:
        try:
            result = repr(e.response.json())
        except:
            result = e.response.text
        # end try
        logger.warning(f'Submitting sticker to getstickers.me failed with error code {e.response.status_code}: {result}')
    except:
        logger.warning('Submitting sticker to getstickers.me failed.', exc_info=True)
    # end try
# end def


# noinspection PyCompatibility
def submit_sticker_message(message: Message):
    if not isinstance(message, Message) or not isinstance(message.sticker, Sticker):
        return
    # end if
    global SEND_CACHE_STICKER
    wrapped_msg = BotMessage(bot_id=sticker_crawl_tbp.user_id, message=message)
    if SEND_CACHE_STICKER.enabled:
        SEND_CACHE_STICKER.queue.append(wrapped_msg)

        if datetime.now() < SEND_CACHE_STICKER.next_send:
            logger.debug(f'Not yet sending the sticker, waiting until {SEND_CACHE_STICKER.next_send}.')
            return
        # end if
        SEND_CACHE_STICKER.next_send = datetime.now() + SEND_INTERVAL
        messages_to_send, SEND_CACHE_STICKER.queue = SEND_CACHE_STICKER.queue, []
    else:
        messages_to_send = [wrapped_msg]
    # end if
    if not messages_to_send:
        logger.debug(f'no stickers, not sending.')
        return
    # end if
    messages_to_send = [msg.to_array() for msg in messages_to_send]
    logger.debug(f'sending {messages_to_send!r} to the API with key={GETSTICKERS_API_KEY!r}.')
    try:
        result = requests.put(
            GETSTICKERS_API_URL + '/submit/stickers',
            params={
                "key": GETSTICKERS_API_KEY,
            },
            json=messages_to_send,
            timeout=TIMEOUT,

        )
        result.raise_for_status()
    except requests.HTTPError as e:
        try:
            result = repr(e.response.json())
        except:
            result = e.response.text
        # end try
        logger.warning(f'Submitting stickers to getstickers.me failed with error code {e.response.status_code}: {result}')
    except:
        logger.warning('Submitting stickers to getstickers.me failed.', exc_info=True)
    # end try
# end def
