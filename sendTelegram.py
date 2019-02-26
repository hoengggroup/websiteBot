import requests

debug = False  # SET TO FALSE FOR DEPLOYMENT!!!

bot_token = '***REMOVED***'
bot_chat_id_debug = '***REMOVED***'  # HWW Free Room Debug
bot_chat_id_shoutout = '***REMOVED***'  # HWW Free Room Shoutout


def bot_sendtext(chat_name, bot_message):
    # send text message
    params = {
        "chat_id": bot_chat_id_debug,
        "text": bot_message,
        "parse_mode": "HTML",
    }

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

    requests.get("https://api.telegram.org/bot"+bot_token+"/sendMessage", params=params)
