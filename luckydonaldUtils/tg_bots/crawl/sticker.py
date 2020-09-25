#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
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
GETSTICKERS_DOMAIN = os.getenv('GETSTICKERS_DOMAIN', 'https://getstickers.me')   # so we can switch to staging there.
GETSTICKERS_ENABLED = GETSTICKERS_API_KEY and GETSTICKERS_DOMAIN

TIMEOUT = 0.5

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
            GETSTICKERS_DOMAIN + '/api/v3/submit/pack/' + pack_url,
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


def submit_sticker_message(message: Message):
    if not isinstance(message, Message) or not isinstance(message.sticker, Sticker):
        return
    # end if
    payload = json.dumps(message.to_array())
    logger.debug(f'sending {payload!r} to the API.')
    try:
        requests.put(
            GETSTICKERS_DOMAIN + '/api/v3/submit/sticker',
            params={
                "key": GETSTICKERS_API_KEY,
                "bot_id": sticker_crawl_tbp.user_id,
            },
            data={
                "message": payload,
            },
            timeout=TIMEOUT,
        )
        return
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

    # so it failed.
    if message.sticker.set_name:
        submit_pack(message.sticker.set_name)
    # end if
# end def
