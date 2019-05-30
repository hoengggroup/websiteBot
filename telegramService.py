# -*- coding: utf-8 -*-

import platform
import sys  # for getting detailed error msg
from itertools import count  # for message numbering

from telegram import Bot, error
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# our libraries
from loggerConfig import create_logger_telegram


# webpages_dict = {}  # needed here or not?, see line 20
admin_chat_ids = {***REMOVED***, ***REMOVED***}

num_messages = count(1)


def set_webpages_dict_reference(the_webpages_dict_reference):
    global webpages_dict
    webpages_dict = the_webpages_dict_reference


def set_add_webpage_reference(the_add_webpage_reference):
    global add_webpage_function
    add_webpage_function = the_add_webpage_reference


def set_remove_webpage_reference(the_remove_webpage_reference):
    global remove_webpage_function
    remove_webpage_function = the_remove_webpage_reference


def start(update, context):
    send_command_reply(update, context, message="Welcome to this website-tracker bot.\nYou can display the available webpages with /webpages and the available commands with /commands.")


def webpages(update, context):
    list_webpages = list(webpages_dict.keys())
    message_list = "\n- "
    message_list += "\n- ".join(list_webpages)
    
    send_command_reply(update, context, message="The available webpages are:" + message_list + "\n\nPlease pay attention to the correct spelling and capitalization.")


def commands(update, context):
    command_list = ("/start\n- display welcome message and lists of available webpages and commands\n"
                    "/webpages\n- display list of available webpages\n"
                    "/commands\n- display this list of available commands\n"
                    "/subscribe {webpage} [webpages]\n- subscribe to notifications about one or more webpages\n"
                    "/unsubscribe {webpage} [webpages]\n- unsubscribe from notifications about one or more webpages\n"
                    "/active\n- show your active subscriptions\n"
                    "/stop\n- unsubscribe from all webpages")

    send_command_reply(update, context, message="The available commands are:\n" + command_list)


def subscribe(update, context):
    webpages = list()
    if context.args:
        webpages += list(context.args)
        for wp in webpages:
            if wp in webpages_dict.keys():
                webpage_object = webpages_dict[wp]
            else:
                send_command_reply(update, context, message="Error. Webpage " + str(wp) + " does not exist in list.")
                continue

            if webpage_object.add_chat_id(chat_id_to_add=update.message.chat_id):
                send_command_reply(update, context, message="You have successfully been subscribed to webpage: " + str(wp))
            else:
                send_command_reply(update, context, message="Error. Subscription to webpage " + str(wp) + " failed.\nTry again or check if you are already subscribed with the /active command.")
    else:
        send_command_reply(update, context, message="Error. You need to specify which webpage you want to subscribe to.")


def unsubscribe(update, context):
    webpages = list()
    if context.args:
        webpages += list(context.args)
        for wp in webpages:
            if wp in webpages_dict.keys():
                webpage_object = webpages_dict[wp]
            else:
                send_command_reply(update, context, message="Error. Webpage " + str(wp) + " does not exist in list.")
                continue

            if webpage_object.remove_chat_id(chat_id_to_remove=update.message.chat_id):
                send_command_reply(update, context, message="You have successfully been unsubscribed from webpage: " + str(wp))
            else:
                send_command_reply(update, context, message="Error. Unsubscription from webpage " + str(wp) + " failed.\nTry again or check if you are already not subscribed with the /active command.")
    else:
        send_command_reply(update, context, message="Error. You need to specify which webpage you want to unsubscribe from.")


def active(update, context):
    webpages = list()
    for wp in list(webpages_dict.keys()):
        webpage_object = webpages_dict[wp]
        if webpage_object.is_chat_id_active(chat_id_to_check=update.message.chat_id):
            webpages.append(wp)

    if webpages:
        message_list = "\n- "
        message_list += "\n- ".join(webpages)
        send_command_reply(update, context, message="You are (still) currently subscribed to the following webpages: " + message_list)
    else:
        send_command_reply(update, context, message="You are (now) not subscribed to any webpages.")


def stop(update, context):
    webpages = list()
    for wp in list(webpages_dict.keys()):
        webpage_object = webpages_dict[wp]
        if webpage_object.remove_chat_id(chat_id_to_remove=update.message.chat_id):
            webpages.append(wp)

    if webpages:
        message_list = "\n- "
        message_list += "\n- ".join(webpages)
        send_command_reply(update, context, message="You have successfully been unsubscribed from the following webpages: " + message_list)
        active(update, context)
        send_command_reply(update, context, message="Goodbye.")
    else:
        send_command_reply(update, context, message="You were not subscribed to any webpages.\nGoodbye.")


def whoami(update, context):
    if update.message.chat_id in admin_chat_ids:
        send_command_reply(update, context, message="Root")
    else:
        send_command_reply(update, context, message="User")


def admincommands(update, context):
    if update.message.chat_id in admin_chat_ids:
        command_list = ("/whoami\n- check admin status (not an inherently privileged command, anyone can check their status)\n"
                        "/admincommands\n- display this list of available admin-only commands\n"
                        "/addwebpage {name} {url} {t_sleep}\n- add a webpage to the list of available webpages\n"
                        "/removewebpage {name}\n- remove a webpage from the list of available webpages\n")

        send_command_reply(update, context, message="The available admin-only commands are:\n" + command_list)
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


def addwebpage(update, context):
    if update.message.chat_id in admin_chat_ids:
        if len(context.args) == 3:
            name = str(context.args[0])
            url = str(context.args[1])
            t_sleep =  int(context.args[2])
            if add_webpage_function(name=name, url=url, t_sleep=t_sleep):
                send_command_reply(update, context, message="The webpage " + name + " has successfully been added to the list.")
            else:
                send_command_reply(update, context, message="Error. Addition of webpage " + name + " failed.\nTry again or check if a webpage with the same name is already on the list with the /webpages command.")
        else:
            send_command_reply(update, context, message="Error. You did not provide the correct arguments for this command (format: \"/addwebpage name url t_sleep\").")
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


def removewebpage(update, context):
    if update.message.chat_id in admin_chat_ids:
        if len(context.args) == 1:
            name = str(context.args[0])
            if remove_webpage_function(name=name):
                send_command_reply(update, context, message="The webpage " + name + " has successfully been removed from the list.")
            else:
                send_command_reply(update, context, message="Error. Removal of webpage " + name + " failed.\nTry again or check if this webpage (with this exact spelling) even exists on the list with the /webpages command.")
        else:
            send_command_reply(update, context, message="Error. You did not provide the correct arguments for this command (format: \"/removewebpage name\").")
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


def text(update, context):
    send_command_reply(update, context, message="Sorry, I only understand commands. Check if you entered a leading slash or get a list of the available commands with /commands.")


def unknown(update, context):
    send_command_reply(update, context, message="Sorry, I did not understand that command. Check the spelling or get a list of the available commands with /commands.")


def send_command_reply(update, context, message):
    logger.debug("Msg to " + str(update.message.chat_id) + "; MSG: " + message)
    if not(message):
        logger.warning("No message.")
        return
    num_this_message = next(num_messages)
    limit = 4096
    warning = "... [truncated]"
    if len(message) > limit:
        logger.warning("Message too long. Sending only the first " + str(limit - len(warning)) + " characters and a [truncated] warning (" + str(limit) + " characters in total).")
        message = message[:(limit - len(warning))] + warning
        logger.debug("New, truncated message: " + message)
    try:
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode="HTML")
        logger.debug("Message #" + str(num_this_message) + " was sent successfully.")
    except error.NetworkError:
        logger.error("Network error when sending message #" + str(num_this_message))
    except:
        logger.error("Unknown error when trying to send telegram message #" + str(num_this_message) + ". The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))


def send_general_broadcast(chat_id, message):
    logger.debug("Msg to " + str(chat_id) + "; MSG: " + message)
    if not(message):
        logger.warning("No message.")
        return
    num_this_message = next(num_messages)
    limit = 4096
    warning = "... [truncated]"
    if len(message) > limit:
        logger.warning("Message too long. Sending only the first " + str(limit - len(warning)) + " characters and a [truncated] warning (" + str(limit) + " characters in total).")
        message = message[:(limit - len(warning))] + warning
        logger.debug("New, truncated message: " + message)
    try:
        bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        logger.debug("Message #" + str(num_this_message) + " was sent successfully.")
    except error.NetworkError:
        logger.error("Network error when sending message #" + str(num_this_message))
    except:
        logger.error("Unknown error when trying to send telegram message #" + str(num_this_message) + ". The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))


def send_admin_broadcast(message):
    admin_message = "[ADMIN BROADCAST] " + message
    for adm_chat_id in admin_chat_ids:
        send_general_broadcast(chat_id=adm_chat_id, message=admin_message)


# this needs to be called to init the telegram service
def init():
    global logger
    logger = create_logger_telegram()

    # needed? at least gets rid of warnings/errors in vscode
    global updater
    global dispatcher
    global bot

    # global webpages_dict  # needed here or not?, see line 20

    if platform.system() == "Linux":
        # @websiteBot_bot
        updater = Updater(token="***REMOVED***", use_context=True)
        dispatcher = updater.dispatcher
        bot = Bot(token="***REMOVED***")
    else:
        # @websiteBotShortTests_bot
        updater = Updater(token="***REMOVED***", use_context=True)
        dispatcher = updater.dispatcher
        bot = Bot(token="***REMOVED***")


    # --- Generally accessible commands:
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("webpages", webpages))
    dispatcher.add_handler(CommandHandler("commands", commands))
    dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dispatcher.add_handler(CommandHandler("active", active))
    dispatcher.add_handler(CommandHandler("stop", stop))
    # --- Privileged admin-only commands:
    # "whoami" is not inherently privileged (anyone can check their status) but we'll not shout it from the rooftops regardless
    dispatcher.add_handler(CommandHandler("whoami", whoami))
    dispatcher.add_handler(CommandHandler("admincommands", admincommands))
    dispatcher.add_handler(CommandHandler("addwebpage", addwebpage))
    dispatcher.add_handler(CommandHandler("removewebpage", removewebpage))
    # --- Catch-all commands for unknown inputs:
    dispatcher.add_handler(MessageHandler(Filters.text, text))
    # The "unknown" handler needs to be added last because it would override any handlers added afterwards
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()

    # Use this command in the python console to clean up the Telegram service when using an IDE that does not handle it well:
    # updater.stop()
