# -*- coding: utf-8 -*-

import platform
import sys  # for getting detailed error msg
from itertools import count  # for message numbering

from telegram import Bot, error, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, Filters

# our libraries
from loggerConfig import create_logger_telegram

from sendPushbullet import send_push
from sendPushbullet import filterset


admin_chat_ids = {***REMOVED***, ***REMOVED***}

num_messages = count(1)

APPLY_NAME_STATE, APPLY_MESSAGE_STATE = range(2)
APPROVE_CHAT_ID_STATE, DENY_CHAT_ID_STATE = range(2)
WPG_NAME_STATE, WPG_URL_STATE, WPG_T_SLEEP_STATE = range(3)


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


### Telegram user flow: start
# access level: none
def start(update, context):
    if create_chat_id_function(chat_id=update.message.chat_id, status=2, user_data=update.message.from_user):
        send_command_reply(update, context, message="Welcome to this website-tracker bot.\nPlease tell me your name and your message to be invited with /apply.\nUntil approval all other functions will remain inaccessible.\nYou can stop this bot and remove your user ID from its list at any time with /stop.")
    else:
        chat_ids_dict[update.message.chat_id].set_user_data(update.message.from_user)
        send_command_reply(update, context, message="You already started this service. If you are not yet approved, please continue with /apply. If you are already approved, check out the available actions with /commands. If you have already been denied, I hope you have a nice day anyway :)")


### Telegram user flow: apply
# access level: none (excluding admins and users)
def apply(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() >= 2:
        update.message.reply_text("Hi. Please tell me your name/nickname/username or send /apply_cancel to stop.")
        return APPLY_NAME_STATE
    else:
        send_command_reply(update, context, message="This command is only intended for new users.")
        return ConversationHandler.END


# conversation helper function for apply()
def apply_name(update, context):
    apply_name = str(update.message.text)
    chat_ids_dict[update.message.chat_id].set_apply_name(apply_name)
    send_command_reply(update, context, message="Ok, "+str(apply_name)+". Please send me your application to use this bot, which I will forward to the admins.")
    return APPLY_MESSAGE_STATE


# conversation helper function for apply()
def apply_message(update, context):
    apply_name = chat_ids_dict[update.message.chat_id].get_apply_name()
    apply_message = str(update.message.text)
    chat_ids_dict[update.message.chat_id].set_apply_message(apply_message)
    message_to_admins = "Application:\n" + str(apply_message) + "\nSent by: " + str(apply_name) + " (" + str(update.message.chat_id) + ")"
    if chat_ids_dict[update.message.chat_id].get_status() == 3:
        message_to_admins += "\nAttention: This user has been denied before."
    for admins in admin_chat_ids:
        send_general_broadcast(chat_id=admins, message=message_to_admins+"\nApprove or deny with /pendingusers.")
    send_command_reply(update, context, message="Alright, I have forwarded your message to the admins. You will hear from me when they have approved (or denied) you.")
    return ConversationHandler.END


# conversation helper function for apply()
def apply_cancel(update, context):
    chat_ids_dict[update.message.chat_id].set_apply_name("")
    chat_ids_dict[update.message.chat_id].set_apply_message("")
    send_command_reply(update, context, message="Bye! You can restart the application at any point with /apply.")
    return ConversationHandler.END


### Telegram admin flow: approve/deny pending users
# access level: admin (0)
def pendingusers(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        chat_ids = chat_ids_dict.keys()
        chat_id_objects = list()
        buttons = list()
        for i, ids in enumerate(chat_ids):
            int_ids = int(ids)
            chat_id_objects.append(chat_ids_dict[int_ids])
            if chat_id_objects[i].get_status() == 2:
                apply_name = chat_id_objects[i].get_apply_name()
                buttons.append(InlineKeyboardButton(apply_name+" ("+str(int_ids)+")", callback_data="user-"+str(int_ids)))
        buttons.append(InlineKeyboardButton("Exit menu", callback_data="exit_users"))
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
        update.message.reply_text("Here is a list of users with pending applications:\nClick for details.", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# callback helper function for pendingusers()
def button_pendingusers_detail(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    callback_user_unstripped = str(query["data"])
    callback_user = int(callback_user_unstripped.replace("user-", ""))
    chat_id_object = chat_ids_dict[callback_user]
    user_info = chat_id_object.get_user_data()
    apply_name = chat_id_object.get_apply_name()
    apply_message = chat_id_object.get_apply_message()
    message = ("User ID: " + str(callback_user) + "\n"
                "Status: 2 (pending)\n"
                "First name: " + str(user_info.first_name) + "\n"
                "Last name: " + str(user_info.last_name) + "\n"
                "Username: " + str(user_info.username) + "\n"
                "Name on application: " + str(apply_name) + "\n"
                "Application: " + str(apply_message))
    buttons = [InlineKeyboardButton("Approve", callback_data="usr_approve-"+str(callback_user)), InlineKeyboardButton("Deny", callback_data="usr_deny-"+str(callback_user))]
    buttons.append(InlineKeyboardButton("Exit menu", callback_data="exit_users"))
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
    bot.edit_message_text(text=message+"\n\nWhat do you want to do with this user?", chat_id=callback_chat_id, message_id=callback_message_id, reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for pendingusers()
def button_pendingusers_approve(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    callback_user_unstripped = str(query["data"])
    callback_user = int(callback_user_unstripped.replace("usr_approve-", ""))
    chat_id_object = chat_ids_dict[callback_user]
    bot.edit_message_text(text="Reopen this menu at any time with /pendingusers.\nYou can also still use /approveuser and /denyuser.", chat_id=callback_chat_id, message_id=callback_message_id)
    if chat_id_object.set_status(new_status=1):
        for admins in admin_chat_ids:
            send_general_broadcast(chat_id=admins, message="Chat ID "+str(callback_user)+" successfully approved (status set to 1).")
        send_general_broadcast(chat_id=callback_user, message="Your application to use this bot was granted. You can now display and subscribe to available webpages with /subscriptions and see the available commands with /commands.")
    else:
        send_command_reply(update, context, message="Error. Setting of new status 1 (approved) for chat ID "+str(callback_user)+" failed.\nThis user may already be approved.\nOtherwise, please try again.")
    bot.answer_callback_query(query["id"])


# callback helper function for pendingusers()
def button_pendingusers_deny(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    callback_user_unstripped = str(query["data"])
    callback_user = int(callback_user_unstripped.replace("usr_deny-", ""))
    chat_id_object = chat_ids_dict[callback_user]
    bot.edit_message_text(text="Reopen this menu at any time with /pendingusers.\nYou can also still use /approveuser and /denyuser.", chat_id=callback_chat_id, message_id=callback_message_id)
    if chat_id_object.set_status(new_status=3):
        for admins in admin_chat_ids:
            send_general_broadcast(chat_id=admins, message="Chat ID "+str(callback_user)+" successfully denied (status set to 3).")
        send_general_broadcast(chat_id=callback_user, message="Sorry, you were denied from using this bot. Goodbye.")
    else:
        send_command_reply(update, context, message="Error. Setting of new status 3 (denied) for chat ID "+str(callback_user)+" failed.\nThis user may already be denied.\nOtherwise, please try again.")
    bot.answer_callback_query(query["id"])


# callback helper function for pendingusers()
def button_pendingusers_exit(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    bot.edit_message_text(text="Reopen this menu at any time with /pendingusers.\nYou can also still use /approveuser and /denyuser.", chat_id=callback_chat_id, message_id=callback_message_id)
    bot.answer_callback_query(query["id"])


### Telegram admin flow: approve users
# access level: admin (0)
def approveuser(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        update.message.reply_text("Which User ID would you like to approve? Otherwise send /user_cancel to stop.")
        return APPROVE_CHAT_ID_STATE
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# conversation helper function for approveuser()
def approve_user_helper(update, context):
    chat_id_to_approve = update.message.text
    try: 
        chat_id_to_approve = int(chat_id_to_approve)
        pass
    except ValueError:
        send_command_reply(update, context, message="Error. This is not a valid chat ID.")
        return ConversationHandler.END
    if chat_id_to_approve in chat_ids_dict.keys():
        chat_id_object = chat_ids_dict[chat_id_to_approve]
        if chat_id_object.set_status(new_status=1):
            for admins in admin_chat_ids:
                send_general_broadcast(chat_id=admins, message="Chat ID "+str(chat_id_to_approve)+" successfully approved (status set to 1).")
            send_general_broadcast(chat_id=chat_id_to_approve, message="Your application to use this bot was granted. You can now display and subscribe to available webpages with /subscriptions and see the available commands with /commands.")
        else:
            send_command_reply(update, context, message="Error. Setting of new status 1 (approved) for chat ID "+str(chat_id_to_approve)+" failed.\nThis user may already be approved.\nOtherwise, please try again.")
    else:
        send_command_reply(update, context, message="Error. Chat ID "+str(chat_id_to_approve)+" does not exist in list.")
    return ConversationHandler.END


### Telegram admin flow: deny users
# access level: admin (0)
def denyuser(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        update.message.reply_text("Which User ID would you like to deny? Otherwise send /user_cancel to stop.")
        return DENY_CHAT_ID_STATE
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# conversation helper function for denyuser()
def deny_user_helper(update, context):
    chat_id_to_deny = update.message.text
    try: 
        chat_id_to_deny = int(chat_id_to_deny)
        pass
    except ValueError:
        send_command_reply(update, context, message="Error. This is not a valid chat ID.")
        return ConversationHandler.END
    if chat_id_to_deny in chat_ids_dict.keys():
        chat_id_object = chat_ids_dict[chat_id_to_deny]
        if chat_id_object.set_status(new_status=3):
            for admins in admin_chat_ids:
                send_general_broadcast(chat_id=admins, message="Chat ID "+str(chat_id_to_deny)+" successfully denied (status set to 3).")
            send_general_broadcast(chat_id=chat_id_to_deny, message="Sorry, you were denied from using this bot. Goodbye.")
        else:
            send_command_reply(update, context, message="Error. Setting of new status 3 (denied) for chat ID "+str(chat_id_to_deny)+" failed.\nThis user may already be denied.\nOtherwise, please try again.")
    else:
        send_command_reply(update, context, message="Error. Chat ID "+str(chat_id_to_deny)+" does not exist in list.")
    return ConversationHandler.END


# conversation helper function for approveuser() and denyuser()
def user_cancel(update, context):
    send_command_reply(update, context, message="Ok. You can approve or deny users at any point with /approveuser or /denyuser.")
    return ConversationHandler.END


### Telegram admin flow: list all users
# access level: admin (0)
def listusers(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        for key, chat_id_object in chat_ids_dict.items():
            print("Current id: " + str(key))
            status = chat_id_object.get_status()
            status_str = status_meaning(status)
            print("Status: " + str(status))
            try:
                user_info = chat_id_object.get_user_data()
                apply_name = chat_id_object.get_apply_name()
                apply_message = chat_id_object.get_apply_message()
                message = ("User ID: " + str(key) + "\n"
                           "Status: " + str(status) + " (" + status_str + ")\n"
                           "First name: " + str(user_info.first_name) + "\n"
                           "Last name: " + str(user_info.last_name) + "\n"
                           "Username: " + str(user_info.username) + "\n"
                           "Name on application: " + str(apply_name) + "\n"
                           "Application: " + str(apply_message))
            except TypeError:
                logger.error("type error user_data unreadable. Presumably uninitialized NoneType.")
                continue
            except AttributeError:
                logger.error("attribute error user_data unreadable. Presumably uninitialized NoneType.")
                message = ("User ID: " + str(key) + "\n"
                           "Status: " + str(status) + " (" + status_str + ")\n"
                           "---Attribute Error---")
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


### Telegram user flow: list all available commands
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
                             "/pendingusers\n- approve or deny pending users who applied to use this bot\n"
                             "/approveuser\n- approve any user\n"
                             "/denyuser\n- deny any user\n"
                             "/listusers\n- get info about all users who are using this bot\n"
                             "/getpageinfo\n- get info about a given webpage\n"
                             "/addwebpage {name} {url} {t_sleep}\n- add a webpage to the list of available webpages\n"
                             "/removewebpage {name}\n- remove a webpage from the list of available webpages")
        send_command_reply(update, context, message="The available commands are:\n"+command_list)
    else:
        send_command_reply(update, context, message="This command is only available to approved users. Sorry.")


### Telegram user flow: list all websites and subscriptions
# access level: user (1)
def subscriptions(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 1:
        reply_markup = build_subscriptions_keyboard(update.message.chat_id)
        send_command_reply(update, context, message="List of available webpages:\n✅ = subscribed, ❌= not subscribed", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to approved users. Sorry.")


# callback helper function for subscriptions()
def button_subscriptions_add(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    callback_webpage_unstripped = str(query["data"])
    callback_webpage = callback_webpage_unstripped.replace("add_subs-", "")
    webpage_object = webpages_dict[callback_webpage]
    if webpage_object.add_chat_id(chat_id_to_add=callback_chat_id):
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        bot.edit_message_text(text="You have successfully been subscribed to webpage: "+str(callback_webpage), chat_id=callback_chat_id, message_id=callback_message_id, reply_markup=reply_markup)
    else:
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        bot.edit_message_text(text="Error. Subscription to webpage "+str(callback_webpage)+" failed.\nPlease try again.", chat_id=callback_chat_id, message_id=callback_message_id, reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for subscriptions()
def button_subscriptions_remove(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    callback_webpage_unstripped = str(query["data"])
    callback_webpage = callback_webpage_unstripped.replace("rem_subs-", "")
    webpage_object = webpages_dict[callback_webpage]
    if webpage_object.remove_chat_id(chat_id_to_remove=callback_chat_id):
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        bot.edit_message_text(text="You have successfully been unsubscribed from webpage: "+str(callback_webpage), chat_id=callback_chat_id, message_id=callback_message_id, reply_markup=reply_markup)
    else:
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        bot.edit_message_text(text="Error. Unsubscription from webpage "+str(callback_webpage)+" failed.\nPlease try again.", chat_id=callback_chat_id, message_id=callback_message_id, reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for subscriptions()
def button_subscriptions_exit(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    bot.edit_message_text(text="Reopen this menu at any time with /subscriptions.", chat_id=callback_chat_id, message_id=callback_message_id)
    bot.answer_callback_query(query["id"])


# helper function for callback helpers for subscriptions()
def build_subscriptions_keyboard(callback_chat_id):
    webpages = webpages_dict.keys()
    webpage_objects = list()
    subscribed = list()
    buttons = list()
    for i, wp in enumerate(webpages):
        webpage_objects.append(webpages_dict[wp])
        if webpage_objects[i].is_chat_id_active(chat_id_to_check=callback_chat_id):
            subscribed.append("✅")
            buttons.append(InlineKeyboardButton(wp, callback_data="rem_subs-"+wp))
            buttons.append(InlineKeyboardButton(subscribed[i], callback_data="rem_subs-"+wp))
        else:
            subscribed.append("❌")
            buttons.append(InlineKeyboardButton(wp, callback_data="add_subs-"+wp))
            buttons.append(InlineKeyboardButton(subscribed[i], callback_data="add_subs-"+wp))
    buttons.append(InlineKeyboardButton("Exit menu", callback_data="exit_subs"))
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
    return reply_markup


### Telegram user flow: stop this bot
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
            send_command_reply(update, context, message="You have successfully been unsubscribed from the following webpages: "+message_list)
        else:
            send_command_reply(update, context, message="You were not subscribed to any webpages.")
    else:
        send_command_reply(update, context, message="You were not subscribed to any webpages because you were not an approved user.")

    if chat_ids_dict[update.message.chat_id].get_status() >= 1:
        if delete_chat_id_function(update.message.chat_id):
            send_command_reply(update, context, message="Your chat ID was removed from this bot. Goodbye.")
        else:
            send_command_reply(update, context, message="Error. Your chat ID could not be removed from this bot. Please try again.")


### Telegram user flow: whoami
# access level: none
def whoami(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() == 0:
        send_command_reply(update, context, message="Root")
    elif chat_ids_dict[update.message.chat_id].get_status() == 1:
        send_command_reply(update, context, message="User")
    else:
        send_command_reply(update, context, message="Guest")


### Telegram admin flow: display info about available websites
# access level: admin (0)
def getpageinfo(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        webpages = webpages_dict.keys()
        webpage_objects = list()
        buttons = list()
        for wp in webpages:
            webpage_objects.append(webpages_dict[wp])
            buttons.append(InlineKeyboardButton(wp, callback_data="webpg_info-"+wp))
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
        send_command_reply(update, context, message="List of webpages:", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# callback helper function for getpageinfo()
def button_getpageinfo(update, context):
    query = update.callback_query
    callback_webpage_unstripped = str(query["data"])
    callback_webpage = callback_webpage_unstripped.replace("webpg_info-", "")
    webpage_object = webpages_dict[callback_webpage]
    callback_chat_id = query["message"]["chat"]["id"]
    send_general_broadcast(chat_id=callback_chat_id, message="Info for webpage \""+str(callback_webpage)+"\":\n"+str(webpage_object))
    bot.answer_callback_query(query["id"])


### Telegram admin flow: add a website to the list
# access level: admin (0)
def addwebpage(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        if len(context.args) == 3:
            name = str(context.args[0])
            url = str(context.args[1])
            t_sleep = int(context.args[2])
            if add_webpage_function(name=name, url=url, t_sleep=t_sleep):
                send_command_reply(update, context, message="The webpage "+str(name)+" has successfully been added to the list.")
            else:
                send_command_reply(update, context, message="Error. Addition of webpage "+str(name)+" failed.\nTry again or check if a webpage with the same name is already on the list with the /subscriptions command.")
        else:
            send_command_reply(update, context, message="Error. You did not provide the correct arguments for this command (format: \"/addwebpage name url t_sleep\").")
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


### Telegram admin flow: remove a website from the list
# access level: admin (0)
def removewebpage(update, context):
    if chat_ids_dict[update.message.chat_id].get_status() <= 0:
        if len(context.args) == 1:
            name = str(context.args[0])
            if remove_webpage_function(name=name):
                send_command_reply(update, context, message="The webpage "+str(name)+" has successfully been removed from the list.")
            else:
                send_command_reply(update, context, message="Error. Removal of webpage "+str(name)+" failed.\nTry again or check if this webpage (with this exact spelling) even exists on the list with the /subscriptions command.")
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
    for filter in filterset:
        if filter in message:
            logger.debug("this message is redirected.")
            send_push("!!!ROOM!!!",message)
            send_admin_broadcast("__") # don't put anything here that is contained in filterset -> inf loop
            return

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
    admin_message = "[ADMIN BROADCAST]\n" + message
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
    # Conversation handler ->:
    conversation_handler_apply = ConversationHandler(
        entry_points=[CommandHandler("apply", apply)],
        states={
            APPLY_NAME_STATE: [MessageHandler(Filters.text, apply_name)],
            APPLY_MESSAGE_STATE: [MessageHandler(Filters.text, apply_message)]
        },
        fallbacks=[CommandHandler("apply_cancel", apply_cancel)]
    )
    dispatcher.add_handler(conversation_handler_apply)
    # --- Approved user accessible commands (access levels 0 and 1):
    dispatcher.add_handler(CommandHandler("commands", commands))
    dispatcher.add_handler(CommandHandler("subscriptions", subscriptions))
    # -> Callback helpers:
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_add, pattern="^add_subs-"))
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_remove, pattern="^rem_subs-"))
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_exit, pattern="exit_subs"))
    dispatcher.add_handler(CommandHandler("stop", stop))
    # --- Privileged admin-only commands (only access level 0):
    # "whoami" is not inherently privileged (anyone can check their status) but we'll not shout it from the rooftops regardless
    dispatcher.add_handler(CommandHandler("whoami", whoami))
    dispatcher.add_handler(CommandHandler("listusers", listusers))
    dispatcher.add_handler(CommandHandler("getpageinfo", getpageinfo))
    # -> Callback helper:
    dispatcher.add_handler(CallbackQueryHandler(button_getpageinfo, pattern="^webpg_info-"))
    dispatcher.add_handler(CommandHandler("addwebpage", addwebpage))
    dispatcher.add_handler(CommandHandler("removewebpage", removewebpage))
    dispatcher.add_handler(CommandHandler("pendingusers", pendingusers))
    # -> Callback helpers:
    dispatcher.add_handler(CallbackQueryHandler(button_pendingusers_approve, pattern="^usr_approve-"))
    dispatcher.add_handler(CallbackQueryHandler(button_pendingusers_deny, pattern="^usr_deny-"))
    dispatcher.add_handler(CallbackQueryHandler(button_pendingusers_detail, pattern="^user-"))
    dispatcher.add_handler(CallbackQueryHandler(button_pendingusers_exit, pattern="exit_users"))
    # Conversation handlers ->:
    conversation_handler_approve_user = ConversationHandler(
        entry_points=[CommandHandler("approveuser", approveuser)],
        states={
            APPROVE_CHAT_ID_STATE: [MessageHandler(Filters.text, approve_user_helper)],
        },
        fallbacks=[CommandHandler("user_cancel", user_cancel)]
    )
    dispatcher.add_handler(conversation_handler_approve_user)
    conversation_handler_deny_user = ConversationHandler(
        entry_points=[CommandHandler("denyuser", denyuser)],
        states={
            DENY_CHAT_ID_STATE: [MessageHandler(Filters.text, deny_user_helper)],
        },
        fallbacks=[CommandHandler("user_cancel", user_cancel)]
    )
    dispatcher.add_handler(conversation_handler_deny_user)
    # --- Catch-all commands for unknown inputs:
    dispatcher.add_handler(MessageHandler(Filters.text, text))
    # The "unknown" handler needs to be added last because it would override any handlers added afterwards
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()

    # Use this command in the python console to clean up the Telegram service when using an IDE that does not handle it well:
    # updater.stop()
