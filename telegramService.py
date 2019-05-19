# -*- coding: utf-8 -*-

from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


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
    context.bot.send_message(chat_id=update.message.chat_id, text="Welcome to this website-tracker bot.\nYou can display the available webpages with /webpages and the available commands with /commands.", parse_mode="HTML")


def webpages(update, context):
    list_webpages = list(webpages_dict.keys())
    message_list = "\n- "
    message_list += "\n- ".join(list_webpages)
    
    context.bot.send_message(chat_id=update.message.chat_id, text="The available webpages are:" + message_list + "\n\nPlease pay attention to the correct spelling and capitalization.", parse_mode="HTML")


def commands(update, context):
    command_list = ("/start\n- display welcome message and lists of available webpages and commands\n"
                    "/webpages\n- display list of available webpages\n"
                    "/commands\n- display this list of available commands\n"
                    "/subscribe {webpage} [webpages]\n- subscribe to notifications about one or more webpages\n"
                    "/unsubscribe {webpage} [webpages]\n- unsubscribe from notifications about one or more webpages\n"
                    "/active\n- show your active subscriptions\n"
                    "/stop\n- unsubscribe from all webpages")

    context.bot.send_message(chat_id=update.message.chat_id, text="The available commands are:\n" + command_list, parse_mode="HTML")


def subscribe(update, context):
    webpages = list()
    if context.args:
        webpages += list(context.args)
        for wp in webpages:
            if wp in webpages_dict.keys():
                webpage_object = webpages_dict[wp]
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Error. Webpage " + str(wp) + " does not exist in list.", parse_mode="HTML")
                continue

            if webpage_object.add_chat_id(chat_id_to_add=update.message.chat_id):
                context.bot.send_message(chat_id=update.message.chat_id, text="You have successfully been subscribed to webpage: " + str(wp), parse_mode="HTML")
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Error. Subscription to webpage " + str(wp) + " failed.\nTry again or check if you are already subscribed with the /active command.", parse_mode="HTML")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Error. You need to specify which webpage you want to subscribe to.", parse_mode="HTML")


def unsubscribe(update, context):
    webpages = list()
    if context.args:
        webpages += list(context.args)
        for wp in webpages:
            if wp in webpages_dict.keys():
                webpage_object = webpages_dict[wp]
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Error. Webpage " + str(wp) + " does not exist in list.", parse_mode="HTML")
                continue

            if webpage_object.remove_chat_id(chat_id_to_remove=update.message.chat_id):
                context.bot.send_message(chat_id=update.message.chat_id, text="You have successfully been unsubscribed from webpage: " + str(wp), parse_mode="HTML")
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Error. Unsubscription from webpage " + str(wp) + " failed.\nTry again or check if you are already not subscribed with the /active command.", parse_mode="HTML")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="Error. You need to specify which webpage you want to unsubscribe from.", parse_mode="HTML")


def active(update, context):
    webpages = list()
    for wp in list(webpages_dict.keys()):
        webpage_object = webpages_dict[wp]
        if webpage_object.is_chat_id_active(chat_id_to_check=update.message.chat_id):
            webpages.append(wp)

    if webpages:
        message_list = "\n- "
        message_list += "\n- ".join(webpages)
        context.bot.send_message(chat_id=update.message.chat_id, text="You are (still) currently subscribed to the following webpages: " + message_list, parse_mode="HTML")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="You are (now) not subscribed to any webpages.", parse_mode="HTML")


def stop(update, context):
    webpages = list()
    for wp in list(webpages_dict.keys()):
        webpage_object = webpages_dict[wp]
        if webpage_object.remove_chat_id(chat_id_to_remove=update.message.chat_id):
            webpages.append(wp)

    if webpages:
        message_list = "\n- "
        message_list += "\n- ".join(webpages)
        context.bot.send_message(chat_id=update.message.chat_id, text="You have successfully been unsubscribed from the following webpages: " + message_list, parse_mode="HTML")
        active(update, context)
        context.bot.send_message(chat_id=update.message.chat_id, text="Goodbye.", parse_mode="HTML")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="You were not subscribed to any webpages.\nGoodbye.", parse_mode="HTML")


def whoami(update, context):
    if update.message.chat_id in admin_chat_ids:
        context.bot.send_message(chat_id=update.message.chat_id, text="Root", parse_mode="HTML")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="User", parse_mode="HTML")


def admincommands(update, context):
    if update.message.chat_id in admin_chat_ids:
        command_list = ("/whoami\n- check admin status (not an inherently privileged command, anyone can check their status)\n"
                        "/admincommands\n- display this list of available admin-only commands\n"
                        "/addwebpage {name} {url} {t_sleep}\n- add a webpage to the list of available webpages\n"
                        "/removewebpage {name}\n- remove a webpage from the list of available webpages\n")

        context.bot.send_message(chat_id=update.message.chat_id, text="The available admin-only commands are:\n" + command_list, parse_mode="HTML")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="This command is only available to admins. Sorry.", parse_mode="HTML")


def addwebpage(update, context):
    if update.message.chat_id in admin_chat_ids:
        if len(context.args) == 3:
            name = str(context.args[0])
            url = str(context.args[1])
            t_sleep = int(context.args[2])
            if add_webpage_function(name=name, url=url, t_sleep=t_sleep):
                context.bot.send_message(chat_id=update.message.chat_id, text="The webpage " + name + " has successfully been added to the list.", parse_mode="HTML")
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Error. Addition of webpage " + name + " failed.\nTry again or check if a webpage with the same name is already on the list with the /webpages command.", parse_mode="HTML")
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Error. You did not provide the correct arguments for this command (format: \"/addwebpage name url t_sleep\").", parse_mode="HTML")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="This command is only available to admins. Sorry.", parse_mode="HTML")


def removewebpage(update, context):
    if update.message.chat_id in admin_chat_ids:
        if len(context.args) == 1:
            name = str(context.args[0])
            if remove_webpage_function(name=name):
                context.bot.send_message(chat_id=update.message.chat_id, text="The webpage " + name + " has successfully been removed from the list.", parse_mode="HTML")
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text="Error. Removal of webpage " + name + " failed.\nTry again or check if this webpage (with this exact spelling) even exists on the list with the /webpages command.", parse_mode="HTML")
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Error. You did not provide the correct arguments for this command (format: \"/removewebpage name\").", parse_mode="HTML")
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text="This command is only available to admins. Sorry.", parse_mode="HTML")


def text(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I only understand commands. Check if you entered a leading slash or get a list of the available commands with /commands.", parse_mode="HTML")


def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I did not understand that command. Check the spelling or get a list of the available commands with /commands.", parse_mode="HTML")


def handler(chat_id, message):
    if not(message):
        return
    bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")


webpages_dict = {}

updater = Updater(token="***REMOVED***", use_context=True)
dispatcher = updater.dispatcher
bot = Bot(token="***REMOVED***")

admin_chat_ids = {***REMOVED***}

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
