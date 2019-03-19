# -*- coding: utf-8 -*-

import requests
import os.path


# CHECK THESE VARIABLES BEFORE DEPLOYMENT!
# Telegram infrastructure
bot_token = '***REMOVED***'
bot_chat_id_debug = '***REMOVED***'
bot_chat_id_shoutout = '***REMOVED***'
# debugging
debug = False

device = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def bot_sendtext(chat_name, logger, bot_message):
    # default payload
    params = {
        "chat_id": bot_chat_id_debug,
        "text": "[" + str(device) + "] " + bot_message,
        "parse_mode": "HTML",
    }

    # special case payloads (shoutout test / shoutout deployment)
    if chat_name == "shoutout":
        if debug:
            params = {
                "chat_id": bot_chat_id_debug,
                "text": "[" + str(device) + "] [SHOUTOUT]: " + bot_message,
                "parse_mode": "HTML",
            }
        else:
            params = {
                "chat_id": bot_chat_id_shoutout,
                "text": "[" + str(device) + "] " + bot_message,
                "parse_mode": "HTML",
            }

    # send payload to Telegram API
    try:
        requests.get("https://api.telegram.org/bot"+bot_token+"/sendMessage", params=params)
    except requests.exceptions.RequestException as e:
        logger.error("[" + str(device) + "] [sendTelegram] RequestException has occured in bot_sendtext.")
        logger.error("[" + str(device) + "] [sendTelegram] The error is: " + str(e))
