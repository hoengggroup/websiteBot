# -*- coding: utf-8 -*-

import platform
import sys  # for getting detailed error msg
from itertools import count  # for message numbering

from telegram import Bot, error, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters

# our libraries
from loggerConfig import create_logger_telegram


admin_chat_ids = {***REMOVED***}#, ***REMOVED***}

num_messages = count(1)


### Interfacing with the main_driver module
def set_webpages_dict_reference(the_webpages_dict_reference):
    global webpages_dict
    webpages_dict = the_webpages_dict_reference


def set_add_webpage_reference(the_add_webpage_reference):
    global add_webpage_function
    add_webpage_function = the_add_webpage_reference


def set_remove_webpage_reference(the_remove_webpage_reference):
    global remove_webpage_function
    remove_webpage_function = the_remove_webpage_reference


def set_chat_ids_dict_reference(the_chat_ids_dict_reference):
    global chat_ids_dict
    chat_ids_dict = the_chat_ids_dict_reference


def set_create_chat_id_reference(the_create_chat_id_reference):
    global create_chat_id_function
    create_chat_id_function = the_create_chat_id_reference


def set_delete_chat_id_reference(the_delete_chat_id_reference):
    global delete_chat_id_function
    delete_chat_id_function = the_delete_chat_id_reference


### Telegram command handlers: user flow
# access level: none
def start(update, context):
    if create_chat_id_function(update.message.chat_id, update.message.from_user):
        send_command_reply(update, context, message="Welcome to this website-tracker bot.\nPlease tell me your name and your message to be invited with /apply {your name and message}\nUntil approval all other functions will remain inaccessible.")
    else:
        chat_ids_dict[update.message.chat_id].set_user_data(update.message.from_user)
        send_command_reply(update, context, message="You already started this service. If you are not yet approved, please continue with /apply. If you are already approved, check out the available actions with /commands. If you have already been denied, I hope you have a nice day anyway :)")


# access level: none (excluding admins and users)
def apply(update, context):
    words = list()
    if chat_ids_dict[update.message.chat_id].get_status() >= 2:
        if context.args:
            words += list(context.args)
            application = " ".join(str(item) for item in words)
            message_to_admins = "Application:\n" + str(application) + "\nSent by: " + str(update.message.chat_id)
            if chat_ids_dict[update.message.chat_id].get_status() == 3:
                message_to_admins += "\nAttention: This user has been denied before."
            for admins in admin_chat_ids:
                send_general_broadcast(chat_id=admins, message=message_to_admins)
        else:
            send_command_reply(update, context, message="Error. You need to send your name and appliction along with this command.")
    else:
        send_command_reply(update, context, message="This command is only intended for new users.")


# access level: admin (0)
def approveuser(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        user_ids = list()
        if context.args:
            user_ids += list(context.args)
            for ids in user_ids:
                int_ids = int(ids)
                if int_ids in chat_ids_dict.keys():
                    chat_id_object = chat_ids_dict[int_ids]
                else:
                    send_command_reply(update, context, message="Error. Chat ID " + str(ids) + " does not exist in list.")
                    continue

                if chat_id_object.set_status(new_status=1):
                    for admins in admin_chat_ids:
                        send_general_broadcast(chat_id=admins, message="Chat ID " + str(ids) + " successfully approved (status set to 1).")
                    send_general_broadcast(chat_id=ids, message="Your application to use this bot was granted. You can now display the available webpages with /webpages and the available commands with /commands")
                else:
                    send_command_reply(update, context, message="Error. Setting of new status 1 (approved) for chat ID " + str(ids) + " failed.\nPlease try again.")
        else:
            send_command_reply(update, context, message="Error. You need to specify which user(s) you want to approve.")
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# access level: admin (0)
def denyuser(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        user_ids = list()
        if context.args:
            user_ids += list(context.args)
            for ids in user_ids:
                int_ids = int(ids)
                if int_ids in chat_ids_dict.keys():
                    chat_id_object = chat_ids_dict[int_ids]
                else:
                    send_command_reply(update, context, message="Error. Chat ID " + str(ids) + " does not exist in list.")
                    continue

                if chat_id_object.set_status(new_status=3):
                    for admins in admin_chat_ids:
                        send_general_broadcast(chat_id=admins, message="Chat ID " + str(ids) + " successfully denied (status set to 3).")
                    send_general_broadcast(chat_id=ids, message="Sorry, you were denied from using this bot. Goodbye.")
                else:
                    send_command_reply(update, context, message="Error. Setting of new status 3 (denied) for chat ID " + str(ids) + " failed.\nPlease try again.")
        else:
            send_command_reply(update, context, message="Error. You need to specify which user(s) you want to deny.")
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# access level: admin (0)
def listusers(update, context):
    print("list users called")
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        for key, chat_id_object in chat_ids_dict.items():
            print("current id: "+str(key))
            int_ids = int(key)
            status = chat_id_object.get_status()
            status_str = status_meaning(status)
            print(status)
            try:
                user_info = chat_id_object.get_user_data()
                message = ("User ID: " + str(key) + "\n"
                           "First Name: " + str(user_info.first_name) + "\n"
                           "Last Name: " + str(user_info.last_name) + "\n"
                           "Username: " + str(user_info.username) + "\n"
                           "Status: " + str(status) + " (" + status_str + ")")
            except TypeError:
                logger.error("type error user_data unreadable. Presumably uninitialized NoneType.")
                continue
            except AttributeError:
                logger.error("attribute error user_data unreadable. Presumably uninitialized NoneType.")
                continue
            except:
                logger.error("Unknown error. The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                continue
            send_command_reply(update, context, message=message)
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# helper function for listusers()
def status_meaning(status):
    if status == 0:
        return "admin"
    elif status == 1:
        return "user"
    elif status == 2:
        return "pending"
    elif status == 3:
        return "denied"
    else:
        return "unknown"


### Telegram command handlers: webpage flow
# access level: admin (0) and user (1)
def commands(update, context):
    command_list = ""
    if chat_ids_dict[update.message.chat_id].get_status() <= 1:
        command_list += ("/start\n- display welcome message and lists of available webpages and commands\n"
                         "/commands\n- display this list of available commands\n"
                         "/subscriptions\n- check your active subscriptions and (un-)subscribe to/from notifications about webpages\n"
                         "/stop\n- unsubscribe from all webpages and remove your user ID from this bot")
        if chat_ids_dict[update.message.chat_id].get_status() <= 0:
            command_list += ("\n\nThe available admin-only commands are:\n"
                             "/whoami\n- check admin status (not an inherently privileged command, anyone can check their status)\n"
                             "/approveuser {chat_id}\n- approve a user who has applied to use this bot\n"
                             "/denyuser {chat_id}\n- deny a user who has applied to use this bot\n"
                             "/listusers\n- get info about all users who are using this bot\n"
                             "/getpageinfo\n- get info about a given webpage\n"
                             "/addwebpage {name} {url} {t_sleep}\n- add a webpage to the list of available webpages\n"
                             "/removewebpage {name}\n- remove a webpage from the list of available webpages")
        send_command_reply(update, context, message="The available commands are:\n" + command_list)
    else:
        send_command_reply(update, context, message="This command is only available to approved users. Sorry.")


# access level: user (1)
def subscriptions(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 1:
        webpages = webpages_dict.keys()
        webpage_objects = list()
        subscribed = list()
        buttons = list()
        for i,wp in enumerate(webpages):
            webpage_objects.append(webpages_dict[wp])
            if webpage_objects[i].is_chat_id_active(chat_id_to_check=update.message.chat_id):
                subscribed.append("✅")
                buttons.append(InlineKeyboardButton(wp, callback_data="rem-"+wp))
                buttons.append(InlineKeyboardButton(subscribed[i], callback_data="rem-"+wp))
            else:
                subscribed.append("❌")
                buttons.append(InlineKeyboardButton(wp, callback_data="add-"+wp))
                buttons.append(InlineKeyboardButton(subscribed[i], callback_data="add-"+wp))
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
        send_command_reply(update, context, message="List of available webpages:\n✅ = subscribed, ❌= not subscribed", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to approved users. Sorry.")


# callback helper function for subscriptions()
def button_subscriptions_add(update, context):
    query = update.callback_query
    callback_webpage_unstripped = str(query['data'])
    callback_webpage = callback_webpage_unstripped.replace("add-", "")
    webpage_object = webpages_dict[callback_webpage]
    callback_chat_id = query['message']['chat']['id']
    if webpage_object.add_chat_id(chat_id_to_add=callback_chat_id):
        send_general_broadcast(chat_id=callback_chat_id, message="You have successfully been subscribed to webpage: " + str(callback_webpage))
    else:
        send_general_broadcast(chat_id=callback_chat_id, message="Error. Subscription to webpage " + str(callback_webpage) + " failed.\nTry again or check if you are already subscribed.")
    bot.answer_callback_query(query['id'])


# callback helper function for subscriptions()
def button_subscriptions_remove(update, context):
    query = update.callback_query
    callback_webpage_unstripped = str(query['data'])
    callback_webpage = callback_webpage_unstripped.replace("rem-", "")
    webpage_object = webpages_dict[callback_webpage]
    callback_chat_id = query['message']['chat']['id']
    if webpage_object.remove_chat_id(chat_id_to_remove=callback_chat_id):
        send_general_broadcast(chat_id=callback_chat_id, message="You have successfully been unsubscribed from webpage: " + str(callback_webpage))
    else:
        send_general_broadcast(chat_id=callback_chat_id, message="Error. Unsubscription from webpage " + str(callback_webpage) + " failed.\nTry again or check if you are already unsubscribed.")
    bot.answer_callback_query(query['id'])


# access level: user (1)
def stop(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 1:
        webpages = list()
        for wp in list(webpages_dict.keys()):
            webpage_object = webpages_dict[wp]
            if webpage_object.remove_chat_id(chat_id_to_remove=update.message.chat_id):
                webpages.append(wp)

        if webpages:
            message_list = "\n- "
            message_list += "\n- ".join(webpages)
            send_command_reply(update, context, message="You have successfully been unsubscribed from the following webpages: " + message_list)
        else:
            send_command_reply(update, context, message="You were not subscribed to any webpages.")
    else:
        send_command_reply(update, context, message="You were not subscribed to any webpages because you were not an approved user.")

    if chat_ids_dict[update.message.chat_id].get_status() >= 1:
        if delete_chat_id_function(update.message.chat_id):
            send_command_reply(update, context, message="Your chat ID was removed from this bot. Goodbye.")
        else:
            send_command_reply(update, context, message="Error. Your chat ID could not be removed from this bot. Please try again.")


### Telegram command handlers: admin flow
# access level: none
def whoami(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() == 0:
        send_command_reply(update, context, message="Root")
    elif chat_ids_dict[update.message.chat_id].get_status() == 1:
        send_command_reply(update, context, message="User")
    else:
        send_command_reply(update, context, message="Guest")


# access level: admin (0)
def getpageinfo(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        webpages = webpages_dict.keys()
        webpage_objects = list()
        buttons = list()
        for wp in webpages:
            webpage_objects.append(webpages_dict[wp])
            buttons.append(InlineKeyboardButton(wp, callback_data="info-"+wp))
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
        send_command_reply(update, context, message="List of webpages:", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# callback helper function for getpageinfo()
def button_getpageinfo(update, context):
    query = update.callback_query
    callback_webpage_unstripped = str(query['data'])
    callback_webpage = callback_webpage_unstripped.replace("info-", "")
    webpage_object = webpages_dict[callback_webpage]
    callback_chat_id = query['message']['chat']['id']
    send_general_broadcast(chat_id=callback_chat_id, message="Info for webpage \"" + str(callback_webpage) + "\":\n" + str(webpage_object))
    bot.answer_callback_query(query['id'])


# access level: admin (0)
def addwebpage(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
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


# access level: admin (0)
def removewebpage(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
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


### Universal helper functions / builtins
# helper function for commands utilizing buttons
def build_menu(buttons, n_cols, header_buttons=False, footer_buttons=False):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


# access level: generic
def text(update, context):
    send_command_reply(update, context, message="Sorry, I only understand commands. Check if you entered a leading slash or get a list of the available commands with /commands.")


# access level: generic
def unknown(update, context):
    send_command_reply(update, context, message="Sorry, I did not understand that command. Check the spelling or get a list of the available commands with /commands.")


# access level: builtin
def send_command_reply(update, context, message, reply_markup=None):
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
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode="HTML", reply_markup=reply_markup)
        logger.debug("Message #" + str(num_this_message) + " was sent successfully.")
    except error.NetworkError:
        logger.error("Network error when sending message #" + str(num_this_message))
    except:
        logger.error("Unknown error when trying to send telegram message #" + str(num_this_message) + ". The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))


# access level: builtin
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


# access level: builtin
def send_admin_broadcast(message):
    admin_message = "[ADMIN BROADCAST] " + message
    for adm_chat_id in admin_chat_ids:
        send_general_broadcast(chat_id=adm_chat_id, message=admin_message)


# this needs to be called from main_driver to make the admins into admins as far as the database is concerned
def escalate_admin_privileges():
    for ids in admin_chat_ids:
        create_chat_id_function(chat_id=ids, status=0)


### Main function
# this needs to be called from main_driver to init the telegram service
def init():
    global logger
    logger = create_logger_telegram()

    # needed? at least gets rid of warnings/errors in vscode
    global updater
    global dispatcher
    global bot
    
    # global webpages_dict  # needed here or not?, see line 24

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


    # --- Generally accessible commands (access levels 0 to 3):
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("apply", apply))
    # --- Approved user accessible commands (access levels 0 and 1):
    dispatcher.add_handler(CommandHandler("commands", commands))
    dispatcher.add_handler(CommandHandler("subscriptions", subscriptions))
    dispatcher.add_handler(CommandHandler("stop", stop))
    # --- Privileged admin-only commands (only access level 0):
    # "whoami" is not inherently privileged (anyone can check their status) but we'll not shout it from the rooftops regardless
    dispatcher.add_handler(CommandHandler("whoami", whoami))
    dispatcher.add_handler(CommandHandler("approveuser", approveuser))
    dispatcher.add_handler(CommandHandler("denyuser", denyuser))
    dispatcher.add_handler(CommandHandler("listusers", listusers))
    dispatcher.add_handler(CommandHandler("getpageinfo", getpageinfo))
    dispatcher.add_handler(CommandHandler("addwebpage", addwebpage))
    dispatcher.add_handler(CommandHandler("removewebpage", removewebpage))
    # --- Callback helper functions:
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_add, pattern='^add-'))
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_remove, pattern='^rem-'))
    dispatcher.add_handler(CallbackQueryHandler(button_getpageinfo, pattern='^info-'))
    # --- Catch-all commands for unknown inputs:
    dispatcher.add_handler(MessageHandler(Filters.text, text))
    # The "unknown" handler needs to be added last because it would override any handlers added afterwards
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()

    # Use this command in the python console to clean up the Telegram service when using an IDE that does not handle it well:
    # updater.stop()
