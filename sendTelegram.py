# -*- coding: utf-8 -*-

import requests
import telegramConfig as telco

# debugging
debug = False


def bot_sendtext(chat_name, logger, bot_message):
    # default payload
    params = {
        "chat_id": telco.bot_chat_id_debug,
        "text": "[DEBUG]\n" + bot_message,
        "parse_mode": "HTML",
    }

    # special case payloads (live test / live deployment)
    if chat_name == "live":
        if debug:
            params = {
                "chat_id": telco.bot_chat_id_debug,
                "text": "[DEBUG]\n" + bot_message,
                "parse_mode": "HTML",
            }
        else:
            params = {
                "chat_id": telco.bot_chat_id_live,
                "text": "[LIVE]\n" + bot_message,
                "parse_mode": "HTML",
            }

    # send payload to Telegram API
    try:
        requests.get("https://api.telegram.org/bot" + telco.bot_token + "/sendMessage", params=params)
    except requests.exceptions.RequestException as e:
        logger.error("[sendTelegram] RequestException has occured in bot_sendtext.")
        logger.error("[sendTelegram] The error is: " + str(e))
