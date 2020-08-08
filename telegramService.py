# -*- coding: utf-8 -*-

# PYTHON BUILTINS
from datetime import datetime  # for setting timestamps
from functools import wraps  # for the decorator function sending the typing state
from itertools import count  # for message numbering
import sys  # for getting detailed error msg

# EXTERNAL LIBRARIES
from telegram import Bot, error, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, Filters
from telegram.error import TelegramError

# OUR OWN LIBRARIES
from configService import filter_dict
from loggerService import create_logger
import databaseService as dbs


# logging
logger = create_logger("tg")


# termination handler (called from termination handler in main_driver)
def exit_cleanup_tg():
    logger.info("Stopping telegram bot instances.")
    print("WAIT FOR THIS PROCESS TO BE COMPLETED.")
    print("SUBSEQUENT KILL SIGNALS WILL BE IGNORED UNTIL TERMINATION ROUTINE HAS FINISHED.")
    try:
        updater.stop()
        logger.info("Successfully stopped telegram bot instances.")
        return True
    except Exception:
        logger.info("Could not stop telegram bot instances.")
        return False


# decorator for sending typing indicators
def send_typing_action(func):
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        return func(update, context, *args, **kwargs)
    return command_func


# error handling
def error_callback(update, context):
    try:
        raise context.error
    except TelegramError as e:
        logger.error("A Telegram-specific error has occured in the telegram bot: " + str(e))
        send_admin_broadcast("A Telegram-specific error has occured in the telegram bot: " + convert_less_than_greater_than(str(e)))
    except Exception as e:
        logger.error("An exception has occured in the telegram bot: " + str(e))
        send_admin_broadcast("An exception has occured in the telegram bot: " + convert_less_than_greater_than(str(e)))


# variable initialization
updater, dispatcher, bot = [None]*3
admin_chat_ids = None
num_messages = count(1)
APPLY_NAME_STATE, APPLY_MESSAGE_STATE = range(2)
STATE_EDITUSER_02_NON_PENDING = range(1)
WS_NAME_STATE, WS_URL_STATE, WS_TIME_SLEEP_STATE = range(3)


##############################################################
#                 Telegram user flow: start                  #
##############################################################

# access level: none
@send_typing_action
def start(update, context):
    if not dbs.db_users_exists(update.message.chat_id):
        dbs.db_users_create(tg_id=update.message.chat_id,
                            status=2,
                            first_name=update.message.from_user['first_name'],
                            last_name=update.message.from_user['last_name'],
                            username=update.message.from_user['username'],
                            apply_name=None,
                            apply_text=None,
                            apply_date=datetime.now())
        send_command_reply(update, context, message="Welcome to this website-tracker bot.\nPlease tell me your name and your message to be invited with /apply.\nUntil approval all other functions will remain inaccessible.\nYou can stop this bot and remove your user ID from its database at any time with /stop.")
    else:
        send_command_reply(update, context, message="You already started this service. If you are not yet approved, please continue with /apply. If you are already approved, check out the available actions with /commands. If you have already been denied, I hope you have a nice day anyway :)")


##############################################################
#                 Telegram user flow: apply                  #
##############################################################

# access level: none (excluding admins and users)
@send_typing_action
def apply(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") >= 2:
        send_command_reply(update, context, message="Hi. Please tell me your name/nickname/username or send /applycancel to stop.")
        return APPLY_NAME_STATE
    else:
        send_command_reply(update, context, message="This command is only intended for new users.")
        return ConversationHandler.END


# conversation helper function for apply()
@send_typing_action
def apply_name(update, context):
    try:
        apply_name = convert_less_than_greater_than(str(update.message.text))
    except ValueError:
        send_command_reply(update, context, message="Error while converting your message to a string. It should be impossible to see this error.")
        return ConversationHandler.END
    dbs.db_users_set_data(tg_id=update.message.chat_id, field="apply_name", argument=apply_name)
    send_command_reply(update, context, message="Ok, " + str(apply_name) + ". Please send me your application to use this bot, which I will forward to the admins.")
    return APPLY_MESSAGE_STATE


# conversation helper function for apply()
@send_typing_action
def apply_message(update, context):
    apply_name = dbs.db_users_get_data(tg_id=update.message.chat_id, field="apply_name")
    try:
        apply_message = convert_less_than_greater_than(str(update.message.text))
    except ValueError:
        send_command_reply(update, context, message="Error while converting your message to a string. It should be impossible to see this error.")
        dbs.db_users_set_data(tg_id=update.message.chat_id, field="apply_name", argument="")
        return ConversationHandler.END
    dbs.db_users_set_data(tg_id=update.message.chat_id, field="apply_text", argument=apply_message)
    message_to_admins = "Application:\n" + str(apply_message) + "\nSent by: " + str(apply_name) + " (" + user_id_linker(update.message.chat_id) + ")"
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") == 3:
        message_to_admins += "\n<i>Attention: This user has been denied before and will not be shown in the pending users section of /edituser. Manual approval would be needed using the approved/denied section of /edituser.</i>"
    else:
        message_to_admins += "\nApprove or deny with /edituser."
    send_admin_broadcast(message_to_admins)
    send_command_reply(update, context, message="Alright, I have forwarded your message to the admins. You will hear from me when they have approved (or denied) you.")
    return ConversationHandler.END


# conversation helper function for apply()
@send_typing_action
def applycancel(update, context):
    dbs.db_users_set_data(tg_id=update.message.chat_id, field="apply_name", argument=None)
    dbs.db_users_set_data(tg_id=update.message.chat_id, field="apply_text", argument=None)
    send_command_reply(update, context, message="Application cancelled. You can restart the application at any point with /apply. You can also completely stop using this bot with /stop.")
    return ConversationHandler.END


##############################################################
#          Telegram admin flow: approve/deny users           #
##############################################################

# access level: admin (0)
@send_typing_action
def edituser(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 0:
        buttons = [InlineKeyboardButton("Pending users", callback_data="edituser_01_pending"), InlineKeyboardButton("Approved/Denied users", callback_data="edituser_01_non_pending"), InlineKeyboardButton("Exit menu", callback_data="edituser_exit")]
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
        send_command_reply(update, context, message="Which kind of user would you like to edit?", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# callback helper function for edituser()
# does functionally the same thing as the edituser command but we need to (almost) duplicate it like this to be able to handle the callback data and edit the message
def button_edituser_back_to_00(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    buttons = [InlineKeyboardButton("Pending users", callback_data="edituser_01_pending"), InlineKeyboardButton("Approved/Denied users", callback_data="edituser_01_non_pending"), InlineKeyboardButton("Exit menu", callback_data="edituser_exit")]
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Which kind of user would you like to edit?", reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for edituser()
def button_edituser_01_pending(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    chat_ids = dbs.db_users_get_pending_ids()
    buttons = list()
    for ids in chat_ids:
        apply_name = dbs.db_users_get_data(tg_id=ids, field="apply_name")
        buttons.append(InlineKeyboardButton(str(apply_name) + " (" + str(ids) + ")", callback_data="edituser_02_pending_detail-" + str(ids)))
    footer_buttons = [InlineKeyboardButton("« Back", callback_data="edituser_back_to_00"), InlineKeyboardButton("Exit menu", callback_data="edituser_exit")]
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1, footer_buttons=footer_buttons))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Here is a list of users with pending applications:\nClick for details.", reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for edituser()
def button_edituser_02_pending_detail(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    query_data_unstripped = str(query["data"])
    query_data = int(query_data_unstripped.replace("edituser_02_pending_detail-", ""))
    user_data = dbs.db_users_get_data(tg_id=query_data)
    message = ("User ID: " + str(query_data) + "\n"
               "Status: 2 (pending)\n"
               "First name: " + str(user_data[2]) + "\n"
               "Last name: " + str(user_data[3]) + "\n"
               "Username: " + str(user_data[4]) + "\n"
               "Name on application: " + str(user_data[5]) + "\n"
               "Application: " + str(user_data[6]) + "\n"
               "Date of application: " + str(user_data[7]))
    buttons = [InlineKeyboardButton("Approve", callback_data="edituser_03_pending_approve-" + str(query_data)), InlineKeyboardButton("Deny", callback_data="edituser_03_pending_deny-" + str(query_data))]
    footer_buttons = [InlineKeyboardButton("« Back", callback_data="edituser_back_to_01_pending"), InlineKeyboardButton("Exit menu", callback_data="edituser_exit")]
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2, footer_buttons=footer_buttons))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message=message + "\n\nWhat do you want to do with this user?", reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for edituser()
def button_edituser_03_pending_approve(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    query_data_unstripped = str(query["data"])
    query_data = int(query_data_unstripped.replace("edituser_03_pending_approve-", ""))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /edituser.")
    if dbs.db_users_set_data(tg_id=query_data, field="status", argument=1):
        send_admin_broadcast("Chat ID " + user_id_linker(query_data) + " successfully approved (status set to 1).")
        send_general_broadcast(chat_id=query_data, message="Your application to use this bot was granted. You can now display and subscribe to available websites with /subscriptions and see the available commands with /commands.")
    else:
        send_command_reply(update, context, message="Error. Setting of new status 1 (approved) for chat ID " + user_id_linker(query_data) + " failed.\nThis user may already be approved.\nOtherwise, please try again.")
    bot.answer_callback_query(query["id"])


# callback helper function for edituser()
def button_edituser_03_pending_deny(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    query_data_unstripped = str(query["data"])
    query_data = int(query_data_unstripped.replace("edituser_03_pending_deny-", ""))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /edituser.")
    if dbs.db_users_set_data(tg_id=query_data, field="status", argument=3):
        send_admin_broadcast("Chat ID " + user_id_linker(query_data) + " successfully denied (status set to 3).")
        send_general_broadcast(chat_id=query_data, message="Sorry, you were denied from using this bot. Goodbye.")
    else:
        send_command_reply(update, context, message="Error. Setting of new status 3 (denied) for chat ID " + user_id_linker(query_data) + " failed.\nThis user may already be denied.\nOtherwise, please try again.")
    bot.answer_callback_query(query["id"])


# callback helper function for edituser()
def button_edituser_01_non_pending(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Which user would you like to edit? Otherwise, send /editusercancel to go back to the menu.")
    bot.answer_callback_query(query["id"])
    return STATE_EDITUSER_02_NON_PENDING


# conversation helper function for edituser()
# does functionally the same thing as the edituser command but we need to (almost) duplicate it like this to be able to handle the conversation state correctly
@send_typing_action
def helper_edituser_back_to_00(update, context):
    buttons = [InlineKeyboardButton("Pending users", callback_data="edituser_01_pending"), InlineKeyboardButton("Approved/Denied users", callback_data="edituser_01_non_pending"), InlineKeyboardButton("Exit menu", callback_data="edituser_exit")]
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
    send_command_reply(update, context, message="Which kind of user would you like to edit?", reply_markup=reply_markup)
    return ConversationHandler.END


# conversation helper function for edituser()
@send_typing_action
def helper_edituser_02_non_pending_detail(update, context):
    chat_id_to_edit = update.message.text
    try:
        chat_id_to_edit = int(chat_id_to_edit)
    except ValueError:
        send_command_reply(update, context, message="Error. This is not a valid chat ID.")
        return ConversationHandler.END
    chat_id_to_edit_status = dbs.db_users_get_data(tg_id=chat_id_to_edit, field="status")
    if chat_id_to_edit in dbs.db_users_get_all_ids() and chat_id_to_edit_status >= 1:
        buttons = list()
        if chat_id_to_edit_status == 1:
            buttons.append(InlineKeyboardButton("Change to status 3 (denied)", callback_data="edituser_03_non_pending_deny-" + str(chat_id_to_edit)))
        elif chat_id_to_edit_status == 3:
            buttons.append(InlineKeyboardButton("Change to status 1 (approved)", callback_data="edituser_03_non_pending_approve-" + str(chat_id_to_edit)))
        else:
            buttons.append(InlineKeyboardButton("Change to status 1 (approved)", callback_data="edituser_03_non_pending_approve-" + str(chat_id_to_edit)))
            buttons.append(InlineKeyboardButton("Change to status 3 (denied)", callback_data="edituser_03_non_pending_deny-" + str(chat_id_to_edit)))
        footer_buttons = [InlineKeyboardButton("« Back", callback_data="edituser_back_to_00"), InlineKeyboardButton("Exit menu", callback_data="edituser_exit")]
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1, footer_buttons=footer_buttons))
        send_command_reply(update, context, message="Current status of this user is: " + str(chat_id_to_edit_status) + " (" + status_meaning(chat_id_to_edit_status) + ")\nWould you like to change the status of this user?", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="Error. Chat ID " + user_id_linker(chat_id_to_edit) + " does not exist in database or is an admin.")
    return ConversationHandler.END


# callback helper function for edituser()
def button_edituser_03_non_pending_approve(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    query_data_unstripped = str(query["data"])
    query_data = int(query_data_unstripped.replace("edituser_03_non_pending_approve-", ""))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /edituser.")
    if dbs.db_users_set_data(tg_id=query_data, field="status", argument=1):
        send_admin_broadcast("Chat ID " + user_id_linker(query_data) + " successfully approved (status set to 1).")
        send_general_broadcast(chat_id=query_data, message="Your application to use this bot was granted. You can now display and subscribe to available websites with /subscriptions and see the available commands with /commands.")
    else:
        send_command_reply(update, context, message="Error. Setting of new status 1 (approved) for chat ID " + user_id_linker(query_data) + " failed.\nPlease try again.")
    bot.answer_callback_query(query["id"])


# callback helper function for edituser()
def button_edituser_03_non_pending_deny(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    query_data_unstripped = str(query["data"])
    query_data = int(query_data_unstripped.replace("edituser_03_non_pending_deny-", ""))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /edituser.")
    if dbs.db_users_set_data(tg_id=query_data, field="status", argument=3):
        send_admin_broadcast("Chat ID " + user_id_linker(query_data) + " successfully denied (status set to 3).")
        send_general_broadcast(chat_id=query_data, message="Sorry, you were denied from using this bot. Goodbye.")
    else:
        send_command_reply(update, context, message="Error. Setting of new status 3 (denied) for chat ID " + user_id_linker(query_data) + " failed.\nPlease try again.")
    bot.answer_callback_query(query["id"])


# callback helper function for edituser()
def button_edituser_exit(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /edituser.")
    bot.answer_callback_query(query["id"])


##############################################################
#            Telegram admin flow: list all users             #
##############################################################

# access level: admin (0)
@send_typing_action
def listusers(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 0:
        for ids in dbs.db_users_get_all_ids():
            user_data = dbs.db_users_get_data(tg_id=ids)
            message = ("User ID: " + user_id_linker(ids) + "\n"
                       "Status: " + str(user_data[1]) + " (" + status_meaning(user_data[1]) + ")\n"
                       "First name: " + str(user_data[2]) + "\n"
                       "Last name: " + str(user_data[3]) + "\n"
                       "Username: " + str(user_data[4]) + "\n")
            if user_data[1] != 0:
                message += ("Name on application: " + str(user_data[5]) + "\n"
                            "Application: " + str(user_data[6]) + "\n"
                            "Date of application: " + str(user_data[7]))
            send_command_reply(update, context, message=message)
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


##############################################################
#      Telegram user flow: list all available commands       #
##############################################################

# access level: admin (0) and user (1)
@send_typing_action
def commands(update, context):
    command_list = ""
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 1:
        command_list += ("/commands -- display this list of available commands\n"
                         "/subscriptions -- manage for which websites you want to receive notifications when they are updated\n"
                         "/stop -- unsubscribe from all websites and remove yourself from this bot")
        if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 0:
            command_list += ("\n\n<b>The available admin-only commands are:</b>\n"
                             "/whoami -- check access status (not admin-only, but hidden)\n"
                             "/edituser -- approve/deny both pending and current users\n"
                             "/listusers -- display information about all users\n"
                             "/getwebsiteinfo -- display information about the available websites\n"
                             "/addwebsite {name} {url} {t_sleep} -- add a website to the list of available websites\n"
                             "/removewebsite {name} -- remove a website from the list of available websites")
        send_command_reply(update, context, message="<b>The available commands are:</b>\n" + command_list)
    else:
        send_command_reply(update, context, message="This command is only available to approved users. Sorry.")


##############################################################
#  Telegram user flow: list all websites and subscriptions   #
##############################################################

# access level: user (1)
@send_typing_action
def subscriptions(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 1:
        reply_markup = build_subscriptions_keyboard(update.message.chat_id)
        send_command_reply(update, context, message="List of available websites:\n✅ = subscribed, ❌= not subscribed", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to approved users. Sorry.")


# callback helper function for subscriptions()
def button_subscriptions_add(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    query_data_unstripped = str(query["data"])
    query_data = query_data_unstripped.replace("add_subs-", "")
    if dbs.db_subscriptions_subscribe(tg_id=callback_chat_id, ws_name=query_data):
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        if reply_markup:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="You have successfully been subscribed to website: " + str(query_data), reply_markup=reply_markup)
        else:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Something went wrong while getting your subscriptions. Please open the menu again with /subscriptions.")
    else:
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        if reply_markup:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Error. Subscription to website " + str(query_data) + " failed.\nThis may be due to duplicate button presses; so you might already be subscribed.\nPlease close and reopen this menu or perform another action to verify your settings.", reply_markup=reply_markup)
        else:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Something went wrong while getting your subscriptions. Please open the menu again with /subscriptions.")
    bot.answer_callback_query(query["id"])


# callback helper function for subscriptions()
def button_subscriptions_remove(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    query_data_unstripped = str(query["data"])
    query_data = query_data_unstripped.replace("rem_subs-", "")
    if dbs.db_subscriptions_unsubscribe(tg_id=callback_chat_id, ws_name=query_data):
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        if reply_markup:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="You have successfully been unsubscribed from website: " + str(query_data), reply_markup=reply_markup)
        else:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Something went wrong while getting your subscriptions. Please open the menu again with /subscriptions.")
    else:
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        if reply_markup:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Error. Unsubscription from website " + str(query_data) + " failed.\nThis may be due to duplicate button presses; so you might already be unsubscribed.\nPlease close and reopen this menu or perform another action to verify your settings.", reply_markup=reply_markup)
        else:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Something went wrong while getting your subscriptions. Please open the menu again with /subscriptions.")
    bot.answer_callback_query(query["id"])


# callback helper function for subscriptions()
def button_subscriptions_exit(update, context):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /subscriptions.")
    bot.answer_callback_query(query["id"])


# helper function for callback helpers for subscriptions()
def build_subscriptions_keyboard(callback_chat_id):
    buttons = list()
    website_ids = dbs.db_websites_get_all_ids()
    for ids in website_ids:
        ws_name = dbs.db_websites_get_name(ids)
        # in case a database query goes wrong, scrap the whole keyboard altogether and let the other functions display an error
        if not ws_name:
            return None
        if dbs.db_subscriptions_check(tg_id=callback_chat_id, ws_id=ids):
            buttons.append(InlineKeyboardButton(ws_name, callback_data="rem_subs-" + ws_name))
            buttons.append(InlineKeyboardButton("✅", callback_data="rem_subs-" + ws_name))
        else:
            buttons.append(InlineKeyboardButton(ws_name, callback_data="add_subs-" + ws_name))
            buttons.append(InlineKeyboardButton("❌", callback_data="add_subs-" + ws_name))
    buttons.append(InlineKeyboardButton("Exit menu", callback_data="exit_subs"))
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=2))
    return reply_markup


##############################################################
#             Telegram user flow: stop this bot              #
##############################################################

# access level: user (1) (and none)
@send_typing_action
def stop(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 1:
        active_subs = list()
        websites_ids = dbs.db_subscriptions_by_user(tg_id=update.message.chat_id)
        for ids in websites_ids:
            ws_name = dbs.db_websites_get_name(ids)
            active_subs.append(ws_name)
        if active_subs:
            active_subs.sort()
            message_list = "\n- "
            message_list += "\n- ".join(active_subs)
            send_command_reply(update, context, message="Your previous subscriptions were: " + message_list)
        else:
            send_command_reply(update, context, message="You were not subscribed to any websites.")
    else:
        send_command_reply(update, context, message="You were not subscribed to any websites because you were not an approved user.")

    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") >= 1:
        if dbs.db_users_delete(tg_id=update.message.chat_id):
            send_command_reply(update, context, message="You were removed from this bot. Goodbye.")
        else:
            send_command_reply(update, context, message="Error. You could not be removed from this bot. Please try again.")


##############################################################
#                 Telegram user flow: whoami                 #
##############################################################

# access level: none
@send_typing_action
def whoami(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") == 0:
        send_command_reply(update, context, message="root")
    elif dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") == 1:
        send_command_reply(update, context, message="user")
    else:
        send_command_reply(update, context, message="guest")


##############################################################
# Telegram admin flow: display info about available websites #
##############################################################

# access level: admin (0)
@send_typing_action
def getwebsiteinfo(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 0:
        websites_ids = dbs.db_websites_get_all_ids()
        buttons = list()
        for ids in websites_ids:
            ws_name = dbs.db_websites_get_name(ids)
            buttons.append(InlineKeyboardButton(ws_name, callback_data="webpg_info-" + ws_name))
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=1))
        send_command_reply(update, context, message="List of websites:", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


# callback helper function for getwebsiteinfo()
@send_typing_action
def button_getwebsiteinfo(update, context):
    query = update.callback_query
    callback_website_unstripped = str(query["data"])
    callback_website = callback_website_unstripped.replace("webpg_info-", "")
    callback_chat_id = query["message"]["chat"]["id"]
    website_data = dbs.db_websites_get_data(ws_name=callback_website)
    message = ("Website ID: " + str(website_data[0]) + "\n"
               "URL: " + str(website_data[2]) + "\n"
               "Sleep time: " + str(website_data[3]) + "\n"
               "Last time checked: " + str(website_data[4]) + "\n"
               "Last time updated: " + str(website_data[5]) + "\n"
               "Last error message: " + convert_less_than_greater_than(str(website_data[6])) + "\n"
               "Last error time: " + str(website_data[7]) + "\n"
               "Subscriptions: " + str(dbs.db_subscriptions_by_website(ws_name=callback_website)) + "\n"
               "Filters: " + str(filter_dict.get(callback_website)))
    send_general_broadcast(chat_id=callback_chat_id, message="Info for website \"" + str(callback_website) + "\":\n" + message)
    bot.answer_callback_query(query["id"])


##############################################################
#       Telegram admin flow: add a website to the list       #
##############################################################

# access level: admin (0)
@send_typing_action
def addwebsite(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 0:
        if len(context.args) == 3:
            try:
                ws_name = convert_less_than_greater_than(str(context.args[0]))
                url = str(context.args[1])
                time_sleep = int(context.args[2])
            except ValueError:
                send_command_reply(update, context, message="Error while parsing your arguments. Check the format and try again.")
                return
            if dbs.db_websites_add(ws_name=ws_name,
                                   url=url,
                                   time_sleep=time_sleep,
                                   last_time_checked=datetime.min,
                                   last_time_updated=datetime.min,
                                   last_error_msg=None,
                                   last_error_time=None,
                                   last_hash=None,
                                   last_content=None):
                send_admin_broadcast("The website " + str(ws_name) + " has successfully been added to the database.")
            else:
                send_command_reply(update, context, message="Error. Addition of website " + str(ws_name) + " failed.\nTry again or check if a website with the same name or url is already in the database with the /subscriptions command.")
        else:
            send_command_reply(update, context, message="Error. You did not provide the correct arguments for this command (format: \"/addwebsite name url t_sleep\").")
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


##############################################################
#    Telegram admin flow: remove a website from the list     #
##############################################################

# access level: admin (0)
@send_typing_action
def removewebsite(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 0:
        if len(context.args) == 1:
            try:
                ws_name = convert_less_than_greater_than(str(context.args[0]))
            except ValueError:
                send_command_reply(update, context, message="Error while converting your message to a string. It should be impossible to see this error.")
                return
            if dbs.db_websites_get_id(ws_name=ws_name):
                if dbs.db_websites_remove(ws_name=ws_name):
                    send_admin_broadcast("The website " + str(ws_name) + " has successfully been removed from the database.")
                else:
                    send_command_reply(update, context, message="Error. Removal of website " + str(ws_name) + " failed.\nTry again or check if this website (with this exact spelling) even exists in the database with the /subscriptions command.")
            else:
                send_command_reply(update, context, message="Error. This website does not exist in the database.")
        else:
            send_command_reply(update, context, message="Error. You did not provide the correct arguments for this command (format: \"/removewebsite name\").")
    else:
        send_command_reply(update, context, message="This command is only available to admins. Sorry.")


##############################################################
#      Telegram user flow: unrecognized message content      #
##############################################################

# access level: generic
@send_typing_action
def unknown_text(update, context):
    send_command_reply(update, context, message="Sorry, I only understand commands. Check if you entered a leading slash or get a list of the available commands with /commands.")


# access level: generic
@send_typing_action
def unknown_command(update, context):
    send_command_reply(update, context, message="Sorry, I did not understand that command. Check the spelling or get a list of the available commands with /commands.")


##############################################################
#                 Universal helper functions                 #
##############################################################

# helper for functions utilizing buttons
def build_menu(buttons, n_cols, header_buttons=False, footer_buttons=False):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


# helper for escaping '<' and '>' because we set message parse_mode to HTML
def convert_less_than_greater_than(unstripped_string):
    stripped_string = unstripped_string.replace("<", "&lt;").replace(">", "&gt;")
    return stripped_string


# helper for converting a user status value to its meaning
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


# helper for making user IDs clickable in messages (if available)
def user_id_linker(chat_id):
    # this only works for users who have set an @username for themselves, otherwise the link url is discarded by the telegram api
    # the link text will not be affected in any case, so we might as well try sending with the link url attached
    return "<a href=\"tg://user?id=" + str(chat_id) + "\">" + str(chat_id) + "</a>"


##############################################################
#             Message-sending wrapper functions              #
##############################################################

# edit previously sent message
def send_message_edit(chat_id, message_id, message, reply_markup=None):
    num_this_message = next(num_messages)
    logger.debug("Message #" + str(num_this_message) + " (edit of message with ID " + str(message_id) + ") to " + str(chat_id) + ":\n" + message)
    if not(message):
        logger.warning("Empty message #" + str(num_this_message) + " (edit of message with ID " + str(message_id) + ") to " + str(chat_id) + ". Not sent.")
        return
    message = truncate_message(message)
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, parse_mode="HTML", reply_markup=reply_markup)
        logger.debug("Message #" + str(num_this_message) + " (edit of message with ID " + str(message_id) + ") to " + str(chat_id) + " was sent successfully.")
    except error.NetworkError as e:
        logger.error("Network error when sending message #" + str(num_this_message) + " (edit of message with ID " + str(message_id) + ") to " + str(chat_id) + ". Details: " + str(e))
    except Exception:
        logger.error("Unknown error when trying to send message #" + str(num_this_message) + " (edit of message with ID " + str(message_id) + ") to " + str(chat_id) + ". The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))


# reply to a command/input from the user
def send_command_reply(update, context, message, reply_markup=None):
    num_this_message = next(num_messages)
    logger.debug("Message #" + str(num_this_message) + " to " + str(update.message.chat_id) + ":\n" + message)
    if not(message):
        logger.warning("Empty message #" + str(num_this_message) + " to " + str(update.message.chat_id) + ". Not sent.")
        return
    message = truncate_message(message)
    try:
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode="HTML", reply_markup=reply_markup)
        logger.debug("Message #" + str(num_this_message) + " to " + str(update.message.chat_id) + " was sent successfully.")
    except error.NetworkError as e:
        logger.error("Network error when sending message #" + str(num_this_message) + " to " + str(update.message.chat_id) + ". Details: " + str(e))
    except Exception:
        logger.error("Unknown error when trying to send message #" + str(num_this_message) + " to " + str(update.message.chat_id) + ". The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))


# send a message (not in reply to input)
def send_general_broadcast(chat_id, message):
    num_this_message = next(num_messages)
    logger.debug("Message #" + str(num_this_message) + " to " + str(chat_id) + ":\n" + message)
    if not(message):
        logger.warning("Empty message #" + str(num_this_message) + " to " + str(chat_id) + ". Not sent.")
        return
    message = truncate_message(message)
    try:
        bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        logger.debug("Message #" + str(num_this_message) + " to " + str(chat_id) + " was sent successfully.")
    except error.NetworkError as e:
        logger.error("Network error when sending message #" + str(num_this_message) + " to " + str(chat_id) + ". Details: " + str(e))
    except Exception:
        logger.error("Unknown error when trying to send message #" + str(num_this_message) + " to " + str(chat_id) + ". The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))


# send a message (not in reply to input) only to admins
def send_admin_broadcast(message):
    admin_message = "[ADMIN BROADCAST]\n" + message
    for adm_chat_id in admin_chat_ids:
        send_general_broadcast(chat_id=adm_chat_id, message=admin_message)


# helper for cleanly truncating message bodies that are too long
def truncate_message(message):
    limit = 4096
    warning = "\n... [truncated]"
    if len(message) > limit:
        message = message[:(limit - len(warning))]  # first truncate to limit...
        message = message[:message.rfind("\n")]  # ...and then truncate to last newline
        logger.warning("Message too long. Sending only the first " + str(len(message)) + " characters and a [truncated] warning (" + str(len(message) + len(warning)) + " characters in total).")
        message += warning
        logger.debug("New, truncated message: " + message)
    return message


##############################################################
#                       Main function                        #
##############################################################

# this needs to be called from main_driver to init the telegram service
def init(is_deployed):
    global updater
    global dispatcher
    global bot

    if is_deployed:
        # @websiteBot_bot
        token = dbs.db_credentials_get_bot_token("websiteBot_bot")
        updater = Updater(token=token, use_context=True)
        dispatcher = updater.dispatcher
        bot = Bot(token=token)
    else:
        # @websiteBotShortTests_bot
        token = dbs.db_credentials_get_bot_token("websiteBotShortTests_bot")
        updater = Updater(token=token, use_context=True)
        dispatcher = updater.dispatcher
        bot = Bot(token=token)

    global admin_chat_ids
    admin_chat_ids = dbs.db_users_get_admins()

    # --- Generally accessible commands (access levels 0 to 3):
    dispatcher.add_handler(CommandHandler("start", start))
    # Conversation handler -->
    conversation_handler_apply = ConversationHandler(
        entry_points=[CommandHandler("apply", apply)],
        states={
            APPLY_NAME_STATE: [MessageHandler(Filters.text & (~ Filters.command), apply_name)],
            APPLY_MESSAGE_STATE: [MessageHandler(Filters.text & (~ Filters.command), apply_message)]
        },
        fallbacks=[CommandHandler("applycancel", applycancel)]
    )
    dispatcher.add_handler(conversation_handler_apply)
    # <--
    # --- Approved user accessible commands (access levels 0 and 1):
    dispatcher.add_handler(CommandHandler("commands", commands))
    dispatcher.add_handler(CommandHandler("subscriptions", subscriptions))
    # Callback helpers -->
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_add, pattern="^add_subs-"))
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_remove, pattern="^rem_subs-"))
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_exit, pattern="exit_subs"))
    # <--
    dispatcher.add_handler(CommandHandler("stop", stop))
    # --- Privileged admin-only commands (only access level 0):
    # "whoami" is not inherently privileged (anyone can check their status) but we'll not shout it from the rooftops regardless
    dispatcher.add_handler(CommandHandler("whoami", whoami))
    dispatcher.add_handler(CommandHandler("edituser", edituser))
    # Callback helpers -->
    dispatcher.add_handler(CallbackQueryHandler(button_edituser_01_pending, pattern="edituser_01_pending"))
    dispatcher.add_handler(CallbackQueryHandler(button_edituser_02_pending_detail, pattern="^edituser_02_pending_detail-"))
    dispatcher.add_handler(CallbackQueryHandler(button_edituser_03_pending_approve, pattern="^edituser_03_pending_approve-"))
    dispatcher.add_handler(CallbackQueryHandler(button_edituser_03_pending_deny, pattern="^edituser_03_pending_deny-"))
    # Conversation handler -->
    conversation_handler_edituser_non_pending = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_edituser_01_non_pending, pattern="edituser_01_non_pending")],
        states={
            STATE_EDITUSER_02_NON_PENDING: [MessageHandler(Filters.text & (~ Filters.command), helper_edituser_02_non_pending_detail)],
        },
        fallbacks=[CommandHandler("editusercancel", helper_edituser_back_to_00)]
    )
    dispatcher.add_handler(conversation_handler_edituser_non_pending)
    # <--
    dispatcher.add_handler(CallbackQueryHandler(button_edituser_03_non_pending_approve, pattern="^edituser_03_non_pending_approve-"))
    dispatcher.add_handler(CallbackQueryHandler(button_edituser_03_non_pending_deny, pattern="^edituser_03_non_pending_deny-"))
    dispatcher.add_handler(CallbackQueryHandler(button_edituser_back_to_00, pattern="edituser_back_to_00"))
    dispatcher.add_handler(CallbackQueryHandler(button_edituser_01_pending, pattern="edituser_back_to_01_pending"))
    dispatcher.add_handler(CallbackQueryHandler(button_edituser_exit, pattern="edituser_exit"))
    # <--
    dispatcher.add_handler(CommandHandler("listusers", listusers))
    dispatcher.add_handler(CommandHandler("getwebsiteinfo", getwebsiteinfo))
    # Callback helper -->
    dispatcher.add_handler(CallbackQueryHandler(button_getwebsiteinfo, pattern="^webpg_info-"))
    # <--
    dispatcher.add_handler(CommandHandler("addwebsite", addwebsite))
    dispatcher.add_handler(CommandHandler("removewebsite", removewebsite))
    # --- Catch-all for unknown inputs (need to be added last):
    dispatcher.add_handler(MessageHandler(Filters.text & (~ Filters.command), unknown_text))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))
    # --- Handler for errors and exceptions in all bot functions
    dispatcher.add_error_handler(error_callback)

    updater.start_polling()
