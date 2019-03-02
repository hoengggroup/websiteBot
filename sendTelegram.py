#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests


# CHECK THESE VARIABLES BEFORE DEPLOYMENT!
# Telegram infrastructure
bot_token = '***REMOVED***'
bot_chat_id_debug = '***REMOVED***'
bot_chat_id_shoutout = '***REMOVED***'
# debugging
debug = False


def bot_sendtext(chat_name, bot_message):
    # default payload
    params = {
        "chat_id": bot_chat_id_debug,
        "text": bot_message,
        "parse_mode": "HTML",
    }

    # special case payloads (shoutout test / shoutout deployment)
    if chat_name == "shoutout":
        if debug:
            params = {
                "chat_id": bot_chat_id_debug,
                "text": "[SHOUTOUT]: " + bot_message,
                "parse_mode": "HTML",
            }
        else:
            params = {
                "chat_id": bot_chat_id_shoutout,
                "text": bot_message,
                "parse_mode": "HTML",
            }

    # send payload to Telegram API
    requests.get("https://api.telegram.org/bot"+bot_token+"/sendMessage", params=params)
