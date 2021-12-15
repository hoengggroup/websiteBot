# -*- coding: utf-8 -*-

# PYTHON BUILTINS
from datetime import datetime  # for setting timestamps
from functools import wraps  # for the decorator function sending the typing state
from itertools import count  # for message numbering
import re  # for regex url validation
# import gettext  # for i18n

# EXTERNAL LIBRARIES
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, Filters
from telegram.error import TelegramError

# OUR OWN LIBRARIES
from module_logging import create_logger, exception_printing
import module_database as dbs


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
        exctype, exc, tb = exception_printing(e)
        logger.error("A telegram.{} has occured in the telegram module.\nError message: {}\nTraceback:\n{}".format(exctype, exc, tb))
        send_admin_broadcast("A telegram.{} has occured in the telegram module.\nError message: {}\nTraceback:\n{}".format(exctype, convert_less_than_greater_than(exc), convert_less_than_greater_than(tb)))
    except Exception as e:
        exctype, exc, tb = exception_printing(e)
        logger.error("A {} has occured in the telegram module.\nError message: {}\nTraceback:\n{}".format(exctype, exc, tb))
        send_admin_broadcast("A {} has occured in the telegram module.\nError message: {}\nTraceback:\n{}".format(exctype, convert_less_than_greater_than(exc), convert_less_than_greater_than(tb)))


# variable initialization
updater, dispatcher, bot = [None]*3
admin_chat_ids = None
num_messages = count(1)
items_per_page = 5
STATE_APPLY_NAME, STATE_APPLY_MESSAGE = range(2)
STATE_WEBSITES_02_ADD_REQUEST_NAME, STATE_WEBSITES_02_ADD_REQUEST_URL, STATE_WEBSITES_02_ADD_REQUEST_TIME_SLEEP = range(3)
STATE_WEBSITES_04_CHANGE_ATTRIBUTE_NAME, STATE_WEBSITES_04_CHANGE_ATTRIBUTE_URL, STATE_WEBSITES_04_CHANGE_ATTRIBUTE_TIME_SLEEP = range(3)
STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_EXPAND, STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_OVERWRITE = range(2)


# URL validation (see https://stackoverflow.com/a/7160778)
regex = re.compile(r'^(?:http)s?://'  # http:// or https://
                   r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
                   r'localhost|'  # localhost...
                   r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                   r'(?::\d+)?'  # optional port
                   r'(?:/?|[/?]\S+)$', re.IGNORECASE)


# i18n
# _ = gettext.gettext


###########################################
#                 /start                  #
###########################################

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
                            start_time=datetime.now())
        send_command_reply(update, context, message=("Welcome to this website-tracker bot.\n"
                                                     "Please tell me your name and your message to be invited with /apply.\n"
                                                     "Until approval all other functions will remain inaccessible.\n"
                                                     "You can stop this bot and remove your user ID from its database at any time with /stop."))
    else:
        send_command_reply(update, context, message=("You already started this service.\n"
                                                     "If you are not yet approved, please continue with /apply.\n"
                                                     "If you are already approved, check out the available actions with /commands.\n"
                                                     "If you have already been denied, I hope you have a nice day anyway :)"))


###########################################
#                 /apply                  #
###########################################

# access level: none (excluding admins and users)
@send_typing_action
def apply(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") >= 2:
        send_command_reply(update, context, message="Hi. Please tell me your name/nickname/username or send /cancel (or any other command) to stop this interaction.")
        context.user_data["conv_state"] = "apply"
        return STATE_APPLY_NAME
    else:
        send_command_reply(update, context, message="This command is only intended for new users.")
        return ConversationHandler.END


# conversation helper function for apply()
@send_typing_action
def apply_name(update, context):
    try:
        apply_name = convert_less_than_greater_than(str(update.message.text))
    except ValueError:
        send_command_reply(update, context, message="This is not a valid string. Try again.")
        return STATE_APPLY_NAME
    dbs.db_users_set_data(tg_id=update.message.chat_id, field="apply_name", argument=apply_name)
    send_command_reply(update, context, message="Ok, {}. Please send me your application to use this bot, which I will forward to the admins. Send /cancel (or any other command) to stop this interaction.".format(apply_name))
    return STATE_APPLY_MESSAGE


# conversation helper function for apply()
@send_typing_action
def apply_message(update, context):
    apply_name = dbs.db_users_get_data(tg_id=update.message.chat_id, field="apply_name")
    try:
        apply_message = convert_less_than_greater_than(str(update.message.text))
    except ValueError:
        send_command_reply(update, context, message="This is not a valid string. Try again.")
        return STATE_APPLY_MESSAGE
    dbs.db_users_set_data(tg_id=update.message.chat_id, field="apply_text", argument=apply_message)
    message_to_admins = "Application by {} ({}):\n".format(apply_name, user_id_linker(update.message.chat_id)) + apply_message
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") == 3:
        message_to_admins += "\n<i>Attention: This user has been denied before and will not be shown in the pending users section of /user. Manual approval would be needed using the denied users section of /user.</i>"
    else:
        message_to_admins += "\nApprove or deny with /user."
    send_admin_broadcast(message_to_admins)
    send_command_reply(update, context, message="Alright, I have forwarded your message to the admins. You will hear from me when they have approved (or denied) you.")
    context.user_data.clear()
    return ConversationHandler.END


###########################################
#                /commands                #
###########################################

# access level: user (1)
@send_typing_action
def commands(update, context):
    command_list = ""
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 1:
        command_list += ("/commands -- display this list of available commands\n"
                         "/subscriptions -- manage for which websites you want to receive notifications when they are updated\n"
                         "/websites -- view info about available websites and request new ones to be added\n"
                         "/user -- view the data this bot currently has saved about you\n"
                         "/stop -- unsubscribe from all websites and remove yourself from this bot")
        if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 0:
            command_list += ("\n\n<b>Available admin-only extensions of commands are:</b>\n"
                             "/websites -- add, remove, or change websites\n"
                             "/user -- view and change the status of users\n\n"
                             "<b>Available admin-only commands are:</b>\n"
                             "servicenotification -- any text after this command will be sent to all users (except status 3)")
        send_command_reply(update, context, message="<b>The available commands are:</b>\n" + command_list)
    else:
        send_command_reply(update, context, message="This command is only available to approved users. Sorry.")


###########################################
#             /subscriptions              #
###########################################

# access level: user (1)
@send_typing_action
def subscriptions(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 1:
        reply_markup = build_subscriptions_keyboard(update.message.chat_id)
        send_command_reply(update, context, message="List of available websites:\nClick the name for additional info about the website and click on the corresponding emoji to toggle your subscription (✅ = subscribed, ❌= not subscribed)", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to approved users. Sorry.")


# callback helper function for subscriptions()
def button_subscriptions_info(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("subs_info-", "")
    website_data = dbs.db_websites_get_data(ws_name=query_data)
    sanitize = dbs.db_users_get_data(tg_id=callback_chat_id, field="status")
    message = generate_website_data_text(website_data, sanitize=sanitize)
    reply_markup = build_subscriptions_keyboard(callback_chat_id)
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="ℹ️ Info for website {}:\n\n{}".format(query_data, message), reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for subscriptions()
def button_subscriptions_add(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("subs_add-", "")
    if dbs.db_subscriptions_subscribe(tg_id=callback_chat_id, ws_name=query_data):
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        if reply_markup:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="You have successfully subscribed to {}".format(query_data), reply_markup=reply_markup)
        else:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Something went wrong while getting your subscriptions. Please open the menu again with /subscriptions.")
    else:
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        if reply_markup:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Error while subscribing you to {}.\nThis may be due to duplicate button presses; so you might already be subscribed.\nPlease close and reopen this menu or perform another action to verify your settings.".format(query_data), reply_markup=reply_markup)
        else:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Something went wrong while getting your subscriptions. Please open the menu again with /subscriptions.")
    bot.answer_callback_query(query["id"])


# callback helper function for subscriptions()
def button_subscriptions_remove(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("subs_rem-", "")
    if dbs.db_subscriptions_unsubscribe(tg_id=callback_chat_id, ws_name=query_data):
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        if reply_markup:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="You have successfully unsubscribed from {}".format(query_data), reply_markup=reply_markup)
        else:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Something went wrong while getting your subscriptions. Please open the menu again with /subscriptions.")
    else:
        reply_markup = build_subscriptions_keyboard(callback_chat_id)
        if reply_markup:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Error while unsubscribing you from {}.\nThis may be due to duplicate button presses; so you might already be unsubscribed.\nPlease close and reopen this menu or perform another action to verify your settings.".format(query_data), reply_markup=reply_markup)
        else:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Something went wrong while getting your subscriptions. Please open the menu again with /subscriptions.")
    bot.answer_callback_query(query["id"])


# callback helper function for subscriptions()
def button_subscriptions_exit(update, context):
    query, callback_chat_id, callback_message_id, __ = extract_query_data(update)
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
        buttons.append(InlineKeyboardButton(ws_name, callback_data="subs_info-{}".format(ws_name)))
        if dbs.db_subscriptions_check(tg_id=callback_chat_id, ws_id=ids):
            buttons.append(InlineKeyboardButton("✅", callback_data="subs_rem-{}".format(ws_name)))
        else:
            buttons.append(InlineKeyboardButton("❌", callback_data="subs_add-{}".format(ws_name)))
    footer_buttons = [[InlineKeyboardButton("Exit menu", callback_data="subs_exit")]]
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, button_cols=2, footer_buttons=footer_buttons))
    return reply_markup


###########################################
#                /websites                #
###########################################

# access level: user (1)
def websites(update, context):
    if update.callback_query:
        query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
        query_page = int(query_data_unstripped.replace("webs_00-", ""))
        callback = True
    else:
        callback_chat_id = update.message.chat_id
        query_page = 1
        callback = False
    if dbs.db_users_get_data(tg_id=callback_chat_id, field="status") <= 1:
        websites_ids = dbs.db_websites_get_all_ids()
        websites_ids_len = len(websites_ids)
        buttons = list()
        for ids in websites_ids[((query_page * items_per_page) - items_per_page):(query_page * items_per_page)]:
            ws_name = dbs.db_websites_get_name(ids)
            buttons.append(InlineKeyboardButton(ws_name, callback_data="webs_01_detail-{}".format(ws_name)))
        if dbs.db_users_get_data(tg_id=callback_chat_id, field="status") == 0:
            header_buttons = [[InlineKeyboardButton("Add website", callback_data="webs_01_add_req")]]
        else:
            header_buttons = [[InlineKeyboardButton("Request website", callback_data="webs_01_add_req")]]
        footer_buttons = [paginator(number_of_items=websites_ids_len, items_per_page=items_per_page, page_number=query_page, callback_base_string="webs_00-")]
        footer_buttons.append([InlineKeyboardButton("Exit menu", callback_data="webs_exit")])
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, button_cols=1, header_buttons=header_buttons, footer_buttons=footer_buttons))
        if callback:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="List of websites:\nClick for more info.", reply_markup=reply_markup)
        else:
            send_command_reply(update, context, message="List of websites:\nClick for more info.", reply_markup=reply_markup)
    else:
        send_command_reply(update, context, message="This command is only available to approved users. Sorry.")
    if callback:
        bot.answer_callback_query(query["id"])


# callback helper function for websites()
def button_websites_submenu_01_add_or_request(update, context):
    __, callback_chat_id, callback_message_id, __ = extract_query_data(update)
    if dbs.db_users_get_data(tg_id=callback_chat_id, field="status") == 0:
        send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Please enter the name of the website you want to add or send /cancel (or any other command) to stop this interaction.")
    else:
        send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="What should be the name of the website you are requesting? Send /cancel (or any other command) to stop this interaction.")
    context.user_data["conv_state"] = "websites"
    return STATE_WEBSITES_02_ADD_REQUEST_NAME


# conversation helper function for websites()
@send_typing_action
def helper_websites_submenu_02_add_or_request_name(update, context):
    new_name = update.message.text
    try:
        new_name = convert_less_than_greater_than(str(new_name))
    except ValueError:
        send_command_reply(update, context, message="This is not a valid string. Try again.")
        return STATE_WEBSITES_02_ADD_REQUEST_NAME
    context.user_data["name"] = new_name
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") == 0:
        send_command_reply(update, context, message="Please enter the URL of the website you want to add or send /cancel (or any other command) to stop this interaction.")
    else:
        send_command_reply(update, context, message="What is the URL of the website you are requesting? Send /cancel (or any other command) to stop this interaction.")
    return STATE_WEBSITES_02_ADD_REQUEST_URL


# conversation helper function for websites()
@send_typing_action
def helper_websites_submenu_02_add_or_request_url(update, context):
    new_url = update.message.text
    try:
        new_url = convert_less_than_greater_than(str(new_url))
    except ValueError:
        send_command_reply(update, context, message="This is not a valid string. Try again.")
        return STATE_WEBSITES_02_ADD_REQUEST_URL
    if re.match(regex, new_url) is None:
        send_command_reply(update, context, message="This is not a valid URL. Try again.")
        return STATE_WEBSITES_02_ADD_REQUEST_URL
    context.user_data["URL"] = new_url
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") == 0:
        send_command_reply(update, context, message="Please enter the sleep time of the website you want to add or send /cancel (or any other command) to stop this interaction.")
    else:
        send_command_reply(update, context, message="How often should the website be checked (time in full seconds)? Send /cancel (or any other command) to stop this interaction.")
    return STATE_WEBSITES_02_ADD_REQUEST_TIME_SLEEP


# conversation helper function for websites()
@send_typing_action
def helper_websites_submenu_02_add_or_request_time_sleep(update, context):
    new_time_sleep = update.message.text
    try:
        new_time_sleep = int(new_time_sleep)
    except ValueError:
        send_command_reply(update, context, message="This is not a valid integer. Try again.")
        return STATE_WEBSITES_02_ADD_REQUEST_TIME_SLEEP
    new_name = context.user_data["name"]
    new_url = context.user_data["URL"]
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") == 0:
        if dbs.db_websites_add(ws_name=new_name,
                               url=new_url,
                               time_sleep=new_time_sleep,
                               last_time_checked=datetime.min,
                               last_time_updated=datetime.min,
                               last_error_msg=None,
                               last_error_time=None,
                               last_hash=None,
                               last_content=None,
                               filters=None):
            send_admin_broadcast("The website {} has successfully been added to the database.".format(new_name))
        else:
            send_command_reply(update, context, message="Error. Addition of website {} failed.\nTry again or check if a website with the same name or url is already in the database.".format(new_name))
    else:
        username = dbs.db_users_get_data(update.message.chat_id, "username")
        message_to_admins = "Website request by user {} ({}):\nSuggested name: {}\nSuggested URL: {}\nSuggested sleep time: {}\n\nAdd manually using /websites.".format(username, user_id_linker(update.message.chat_id), new_name, new_url, new_time_sleep)
        send_admin_broadcast(message_to_admins)
        send_command_reply(update, context, message="Alright, I have forwarded your request to the admins. Check back later whether your request was added with /subscriptions.")
    context.user_data.clear()
    return ConversationHandler.END


# callback helper function for websites()
def button_websites_submenu_01_detail(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("webs_01_detail-", "")
    website_data = dbs.db_websites_get_data(ws_name=query_data)
    if dbs.db_users_get_data(tg_id=callback_chat_id, field="status") == 0:
        message = generate_website_data_text(website_data)
        buttons = [InlineKeyboardButton("Change attributes", callback_data="webs_02_attr-{}".format(query_data)),
                   InlineKeyboardButton("Delete website", callback_data="webs_02_del-{}".format(query_data))]
    else:
        buttons = []
        message = generate_website_data_text(website_data, sanitize=True)
    footer_buttons = [[InlineKeyboardButton("« Back", callback_data="webs_00-1"),
                       InlineKeyboardButton("Exit menu", callback_data="webs_exit")]]
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, button_cols=1, footer_buttons=footer_buttons))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message=message, reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for websites()
def button_websites_submenu_02_delete(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    print(query_data_unstripped)
    query_data = query_data_unstripped.replace("webs_02_del-", "")
    print(query_data)
    buttons = [InlineKeyboardButton("Confirm deletion", callback_data="webs_03_del-{}".format(query_data))]
    footer_buttons = [[InlineKeyboardButton("« Back", callback_data="webs_01_detail-{}".format(query_data)),
                       InlineKeyboardButton("Exit menu", callback_data="webs_exit")]]
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, button_cols=1, footer_buttons=footer_buttons))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="This website and all associated data will be irrevocably deleted from the database.\nAre you sure?", reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for websites()
def button_websites_submenu_03_delete_confirm(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("webs_03_del-", "")
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /websites.")
    if dbs.db_websites_remove(ws_name=query_data):
        send_admin_broadcast("The website {} has successfully been removed from the database.".format(query_data))
    else:
        send_command_reply(update, context, message="Error. Removal of website {} failed.".format(query_data))
    bot.answer_callback_query(query["id"])


# callback helper function for websites()
def button_websites_submenu_02_edit_attributes(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("webs_02_attr-", "")
    buttons = [InlineKeyboardButton("Name", callback_data="webs_03_attr-name-{}".format(query_data)),
               InlineKeyboardButton("URL", callback_data="webs_03_attr-url-{}".format(query_data)),
               InlineKeyboardButton("Sleep time", callback_data="webs_03_attr-tsleep-{}".format(query_data)),
               InlineKeyboardButton("Filters", callback_data="webs_03_attr-filt-{}".format(query_data))]
    footer_buttons = [[InlineKeyboardButton("« Back", callback_data="webs_01_detail-{}".format(query_data)),
                       InlineKeyboardButton("Exit menu", callback_data="webs_exit")]]
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, button_cols=1, footer_buttons=footer_buttons))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Which attribute would you like to change?", reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for websites()
def button_websites_submenu_03_change_attribute(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("webs_03_attr-", "")
    query_type, query_ws_name = query_data.split("-", 1)
    reply_markup = None
    if query_type == "name":
        message = "The current name is: {}\nWhat should be the new name?\nSend /cancel (or any other command) to stop this interaction.".format(query_ws_name)
        state = STATE_WEBSITES_04_CHANGE_ATTRIBUTE_NAME
    elif query_type == "url":
        message = "The current URL of the website {} is: {}\nWhat should be the new URL?\nSend /cancel (or any other command) to stop this interaction.".format(query_ws_name, dbs.db_websites_get_data(ws_name=str(query_ws_name), field="url"))
        state = STATE_WEBSITES_04_CHANGE_ATTRIBUTE_URL
    elif query_type == "tsleep":
        message = "The current sleep time of the website {} is: {}\nWhat should be the new sleep time?\nSend /cancel (or any other command) to stop this interaction.".format(query_ws_name, dbs.db_websites_get_data(ws_name=str(query_ws_name), field="time_sleep"))
        state = STATE_WEBSITES_04_CHANGE_ATTRIBUTE_TIME_SLEEP
    elif query_type == "filt":
        message = "The current filters of the website {} are: {}\nWhat do you want to do?".format(query_ws_name, unpack_filters(dbs.db_websites_get_data(ws_name=str(query_ws_name), field="filters")))
        buttons = [InlineKeyboardButton("Remove filters", callback_data="webs_04_attr_filt-rem-{}".format(query_ws_name)),
                   InlineKeyboardButton("Expand filters", callback_data="webs_04_attr_filt-exp-{}".format(query_ws_name)),
                   InlineKeyboardButton("Overwrite filters", callback_data="webs_04_attr_filt-ove-{}".format(query_ws_name))]
        footer_buttons = [[InlineKeyboardButton("« Back", callback_data="webs_02_attr-{}".format(query_ws_name)),
                           InlineKeyboardButton("Exit menu", callback_data="webs_exit")]]
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, button_cols=1, footer_buttons=footer_buttons))
        state = ConversationHandler.END
    else:
        message = "Invalid attribute. Please try again."
        state = ConversationHandler.END
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message=message, reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])
    if query_type != "filt":
        context.user_data["conv_state"] = "websites"
        context.user_data["query_ws_name"] = query_ws_name
    return state


# conversation helper function for websites()
@send_typing_action
def helper_websites_submenu_04_change_attribute_name(update, context):
    new_name = update.message.text
    try:
        new_name = convert_less_than_greater_than(str(new_name))
    except ValueError:
        send_command_reply(update, context, message="This is not a valid string. Try again.")
        return STATE_WEBSITES_04_CHANGE_ATTRIBUTE_NAME
    ws_name_to_edit = context.user_data["query_ws_name"]
    if dbs.db_websites_set_data(ws_name=ws_name_to_edit, field="ws_name", argument=new_name):
        send_admin_broadcast("Website {} was successfully renamed to {}.".format(ws_name_to_edit, new_name))
    else:
        send_command_reply(update, context, message="Error. Setting of new name {} for website {} failed.\nTry again or check if a website with the same name is already in the database.".format(new_name, ws_name_to_edit))
    context.user_data.clear()
    return ConversationHandler.END


# conversation helper function for websites()
@send_typing_action
def helper_websites_submenu_04_change_attribute_url(update, context):
    new_url = update.message.text
    try:
        new_url = convert_less_than_greater_than(str(new_url))
    except ValueError:
        send_command_reply(update, context, message="This is not a valid string. Try again.")
        return STATE_WEBSITES_04_CHANGE_ATTRIBUTE_URL
    if re.match(regex, new_url) is None:
        send_command_reply(update, context, message="This is not a valid URL. Try again.")
        return STATE_WEBSITES_04_CHANGE_ATTRIBUTE_URL
    ws_name_to_edit = context.user_data["query_ws_name"]
    if dbs.db_websites_set_data(ws_name=ws_name_to_edit, field="url", argument=new_url):
        send_admin_broadcast("URL of website {} was successfully changed to {}.".format(ws_name_to_edit, new_url))
    else:
        send_command_reply(update, context, message="Error. Setting of new URL {} for website {} failed.\nTry again or check if a website with the same url is already in the database.".format(new_url, ws_name_to_edit))
    context.user_data.clear()
    return ConversationHandler.END


# conversation helper function for websites()
@send_typing_action
def helper_websites_submenu_04_change_attribute_time_sleep(update, context):
    new_time_sleep = update.message.text
    try:
        new_time_sleep = int(new_time_sleep)
    except ValueError:
        send_command_reply(update, context, message="This is not a valid integer. Try again.")
        return STATE_WEBSITES_04_CHANGE_ATTRIBUTE_TIME_SLEEP
    ws_name_to_edit = context.user_data["query_ws_name"]
    if dbs.db_websites_set_data(ws_name=ws_name_to_edit, field="time_sleep", argument=new_time_sleep):
        send_admin_broadcast("Sleep time of website {} was successfully changed to {}.".format(ws_name_to_edit, new_time_sleep))
    else:
        send_command_reply(update, context, message="Error. Setting of new sleep time {} for website {} failed.\nPlease try again.".format(new_time_sleep, ws_name_to_edit))
    context.user_data.clear()
    return ConversationHandler.END


# callback helper function for websites()
def button_websites_submenu_04_change_attribute_filters(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("webs_04_attr_filt-", "")
    query_type, query_ws_name = query_data.split("-", 1)
    if query_type == "rem":
        send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /websites.")
        if dbs.db_websites_set_data(ws_name=query_ws_name, field="filters", argument=None):
            send_admin_broadcast("Filters for website {} were successfully deleted.".format(query_ws_name))
        else:
            send_command_reply(update, context, message="Error. Deletion of filters for website {} failed.\nPlease try again.".format(query_ws_name))
        context.user_data.clear()
        state = ConversationHandler.END
    elif query_type == "exp":
        send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Which filters do you want to add? (Use comma separation without spaces.)\nSend /cancel (or any other command) to stop this interaction.")
        state = STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_EXPAND
    elif query_type == "ove":
        send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Which should be the new filters? (Use comma separation without spaces.)\nSend /cancel (or any other command) to stop this interaction.")
        state = STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_OVERWRITE
    else:
        send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Invalid attribute. Please try again.")
        context.user_data.clear()
        state = ConversationHandler.END
    bot.answer_callback_query(query["id"])
    if query_type != "rem":
        context.user_data["query_ws_name"] = query_ws_name
    return state


# conversation helper function for websites()
@send_typing_action
def helper_websites_submenu_05_change_attribute_filters_expand(update, context):
    new_filters = update.message.text
    try:
        new_filters = str(new_filters)
    except ValueError:
        send_command_reply(update, context, message="This is not a valid string. Please try again.")
        return STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_EXPAND
    new_filters = unpack_filters(new_filters)
    if new_filters is None:
        send_command_reply(update, context, message="This is an empty or invalid list. Please try again.")
        return STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_EXPAND
    ws_name_to_edit = context.user_data["query_ws_name"]
    filters_list = list()
    old_filters = unpack_filters(dbs.db_websites_get_data(ws_name=ws_name_to_edit, field="filters"))
    if old_filters is not None:
        filters_list.extend(old_filters)
    filters_list.extend(new_filters)
    if dbs.db_websites_set_data(ws_name=ws_name_to_edit, field="filters", argument=repack_filters(filters_list)):
        send_admin_broadcast("Filters for website {} were successfully expanded to {}.".format(ws_name_to_edit, filters_list))
    else:
        send_command_reply(update, context, message="Error. Setting of new filters {} for website {} failed.\nPlease try again.".format(filters_list, ws_name_to_edit))
    context.user_data.clear()
    return ConversationHandler.END


# conversation helper function for websites()
@send_typing_action
def helper_websites_submenu_05_change_attribute_filters_overwrite(update, context):
    new_filters = update.message.text
    try:
        new_filters = str(new_filters)
    except ValueError:
        send_command_reply(update, context, message="This is not a valid string. Please try again.")
        return STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_OVERWRITE
    new_filters = unpack_filters(new_filters)
    if new_filters is None:
        send_command_reply(update, context, message="This is an empty or invalid list. Please try again.")
        return STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_OVERWRITE
    ws_name_to_edit = context.user_data["query_ws_name"]
    filters_list = list()
    filters_list.extend(new_filters)
    if dbs.db_websites_set_data(ws_name=ws_name_to_edit, field="filters", argument=repack_filters(filters_list)):
        send_admin_broadcast("Filters for website {} were successfully changed to {}.".format(ws_name_to_edit, filters_list))
    else:
        send_command_reply(update, context, message="Error. Setting of new filters {} for website {} failed.\nPlease try again.".format(filters_list, ws_name_to_edit))
    context.user_data.clear()
    return ConversationHandler.END


# callback helper function for websites()
def button_websites_exit(update, context):
    query, callback_chat_id, callback_message_id, __ = extract_query_data(update)
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /websites.")
    bot.answer_callback_query(query["id"])


###########################################
#                  /user                  #
###########################################

# access level: user (1)
def user(update, context):
    if update.callback_query:
        query, callback_chat_id, callback_message_id, __ = extract_query_data(update)
        callback = True
    else:
        callback_chat_id = update.message.chat_id
        callback = False
    if dbs.db_users_get_data(tg_id=callback_chat_id, field="status") <= 0:
        buttons = [InlineKeyboardButton("Admins (status 0)", callback_data="usr_01-0#1"),
                   InlineKeyboardButton("Approved users (status 1)", callback_data="usr_01-1#1"),
                   InlineKeyboardButton("Pending users (status 2)", callback_data="usr_01-2#1"),
                   InlineKeyboardButton("Denied users (status 3)", callback_data="usr_01-3#1"),
                   InlineKeyboardButton("Exit menu", callback_data="usr_exit")]
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, button_cols=1))
        if callback:
            send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Which kind of user would you like to view/edit?", reply_markup=reply_markup)
        else:
            send_command_reply(update, context, message="Which kind of user would you like to view/edit?", reply_markup=reply_markup)
    else:
        user_data = dbs.db_users_get_data(tg_id=callback_chat_id)
        message = generate_user_data_text(user_data, sanitize=True)
        send_command_reply(update, context, message="This bot currently has the following data saved about you. Delete this data and stop using the bot at any time with /stop.\n\n" + message)
    if callback:
        bot.answer_callback_query(query["id"])


# callback helper function for user()
def button_user_submenu_01(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("usr_01-", "")
    query_status, query_page = (int(x) for x in query_data.split("#"))
    chat_ids = dbs.db_users_get_all_ids_with_status(query_status)
    chat_ids_len = len(chat_ids)
    buttons = list()
    for ids in chat_ids[((query_page * items_per_page) - items_per_page):(query_page * items_per_page)]:
        if query_status == 0:
            name = dbs.db_users_get_data(tg_id=ids, field="first_name")
        else:
            name = dbs.db_users_get_data(tg_id=ids, field="apply_name")
        buttons.append(InlineKeyboardButton("{} ({})".format(name, ids), callback_data="usr_02-{}".format(ids)))
    footer_buttons = [paginator(number_of_items=chat_ids_len, items_per_page=items_per_page, page_number=query_page, callback_base_string="usr_01-{}#".format(query_status))]
    footer_buttons.append([InlineKeyboardButton("« Back", callback_data="usr_00"),
                           InlineKeyboardButton("Exit menu", callback_data="usr_exit")])
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, button_cols=1, footer_buttons=footer_buttons))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Here is a list of users with status {}:\nClick for details.".format(query_status), reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for user()
def button_user_submenu_02(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = int(query_data_unstripped.replace("usr_02-", ""))
    user_data = dbs.db_users_get_data(tg_id=query_data)
    message = generate_user_data_text(user_data)
    buttons = list()
    if user_data[1] >= 1:
        message += "\n\n<b>The current status of this user is: {} ({})</b>\nWould you like to change the status of this user?".format(user_data[1], status_meaning(user_data[1]))
        if user_data[1] >= 2:
            buttons.append(InlineKeyboardButton("Change to status 1 (approved)", callback_data="usr_03-appr-{}".format(query_data)))
        if user_data[1] <= 2:
            buttons.append(InlineKeyboardButton("Change to status 3 (denied)", callback_data="usr_03-deny-{}".format(query_data)))
    footer_buttons = [[InlineKeyboardButton("« Back", callback_data="usr_01-{}#1".format(user_data[1])),
                       InlineKeyboardButton("Exit menu", callback_data="usr_exit")]]
    reply_markup = InlineKeyboardMarkup(build_menu(buttons, button_cols=1, footer_buttons=footer_buttons))
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message=message, reply_markup=reply_markup)
    bot.answer_callback_query(query["id"])


# callback helper function for user()
def button_user_submenu_03(update, context):
    query, callback_chat_id, callback_message_id, query_data_unstripped = extract_query_data(update)
    query_data = query_data_unstripped.replace("usr_03-", "")
    query_approve_deny, query_chat_id = query_data.split("-")
    query_chat_id = int(query_chat_id)
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /user.")
    if query_approve_deny == "appr":
        if dbs.db_users_set_data(tg_id=query_chat_id, field="status", argument=1):
            send_admin_broadcast("Chat ID {} successfully approved (status set to 1).".format(user_id_linker(query_chat_id)))
            send_general_broadcast(chat_id=query_chat_id, message="Your application to use this bot was granted. You can now display and subscribe to available websites with /subscriptions and see the available commands with /commands.")
        else:
            send_command_reply(update, context, message="Error. Setting of new status 1 (approved) for chat ID {} failed.\nPlease try again.".format(user_id_linker(query_chat_id)))
    else:
        if dbs.db_users_set_data(tg_id=query_chat_id, field="status", argument=3):
            send_admin_broadcast("Chat ID {} successfully denied (status set to 3).".format(user_id_linker(query_chat_id)))
            send_general_broadcast(chat_id=query_chat_id, message="Sorry, you were denied from using this bot. Goodbye.")
        else:
            send_command_reply(update, context, message="Error. Setting of new status 3 (denied) for chat ID {} failed.\nPlease try again.".format(user_id_linker(query_chat_id)))
    bot.answer_callback_query(query["id"])


# callback helper function for user()
def button_user_exit(update, context):
    query, callback_chat_id, callback_message_id, __ = extract_query_data(update)
    send_message_edit(chat_id=callback_chat_id, message_id=callback_message_id, message="Reopen this menu at any time with /user.")
    bot.answer_callback_query(query["id"])


###########################################
#                  /stop                  #
###########################################

# access level: none (admins will not be deleted but can reset subscriptions)
@send_typing_action
def stop(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 1:
        message_list = generate_user_subscriptions_list(update.message.chat_id)
        if message_list:
            send_command_reply(update, context, message="Your previous subscriptions were: {}".format(message_list))
        else:
            send_command_reply(update, context, message="You were not subscribed to any websites.")
    else:
        send_command_reply(update, context, message="You were not subscribed to any websites because you were not an approved user.")

    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") >= 1:
        if dbs.db_users_delete(tg_id=update.message.chat_id):
            send_command_reply(update, context, message="You were removed from this bot. Goodbye.\nStart using this bot again at any time by sending /start.")
        else:
            send_command_reply(update, context, message="Error. Something went wrong while trying to remove you from this bot. Please try again.")


###########################################
#          /servicenotification           #
###########################################

def servicenotification(update, context):
    if dbs.db_users_get_data(tg_id=update.message.chat_id, field="status") <= 0:
        if context.args:
            try:
                words = list(context.args)
                message = " ".join(str(item) for item in words)
                send_service_message(message)
            except ValueError:
                send_command_reply(update, context, message="This is not a valid string.")
        else:
            send_command_reply(update, context, message="This command needs arguments (the message) alongside it.")


###########################################
#     /cancel (conversation fallback)     #
###########################################

# access level: generic
@send_typing_action
def cancel(update, context):
    if context.user_data.get("conv_state") == "apply":
        dbs.db_users_set_data(tg_id=update.message.chat_id, field="apply_name", argument=None)
        dbs.db_users_set_data(tg_id=update.message.chat_id, field="apply_text", argument=None)
        send_command_reply(update, context, message="Application cancelled. You can restart the application at any point with /apply. You can also completely stop using this bot with /stop.")
    else:
        send_command_reply(update, context, message="Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


###########################################
#          Unrecognized commands          #
###########################################

# access level: generic
@send_typing_action
def unknown_command(update, context):
    send_command_reply(update, context, message="Sorry, I did not understand that command. Check the spelling or get a list of the available commands with /commands.")


###########################################
#       Universal helper functions        #
###########################################

# helper for functions utilizing buttons
def build_menu(buttons, button_cols, header_buttons=False, footer_buttons=False):
    """ Build the button layout for a button keyboard.

    Parameters:
        buttons (list): individual buttons which make up the main part of the keyboard.
        button_cols (int): number of colums in the main part of the keyboard.

    Keyword arguments:
        header_buttons (list(list)): list of lists (rows) which make up the header of the keyboard (the rows can have different numbers of elements, i.e. buttons). Default: False
        footer_buttons (list(list)): list of lists (rows) which make up the footer of the keyboard (the rows can have different numbers of elements, i.e. buttons). Default: False

    Returns:
        menu (list(list)): list of lists (rows) which make up the entire keyboard (the rows can have different numbers of elements, i.e. buttons).
    """
    menu = [buttons[i:i + button_cols] for i in range(0, len(buttons), button_cols)]
    if header_buttons:
        menu = header_buttons + menu
    if footer_buttons:
        menu.extend(footer_buttons)
    return menu


# helper for functions with lists that need pagination
def paginator(number_of_items, items_per_page, page_number, callback_base_string):
    page_buttons = list()
    if number_of_items > items_per_page:
        if (page_number - 1) <= 0:
            page_buttons = [InlineKeyboardButton("→ Next", callback_data=callback_base_string + str(page_number + 1))]
        elif (page_number + 1) * 5 >= number_of_items:
            page_buttons = [InlineKeyboardButton("← Prev", callback_data=callback_base_string + str(page_number - 1))]
        else:
            page_buttons = [InlineKeyboardButton("← Prev", callback_data=callback_base_string + str(page_number - 1)),
                            InlineKeyboardButton("→ Next", callback_data=callback_base_string + str(page_number + 1))]
    return page_buttons


# helper for callback functions
def extract_query_data(update):
    query = update.callback_query
    callback_chat_id = query["message"]["chat"]["id"]
    callback_message_id = query["message"]["message_id"]
    query_data_unstripped = str(query["data"])
    return query, callback_chat_id, callback_message_id, query_data_unstripped


# helper for listing a user's active subscriptions
def generate_user_subscriptions_list(tg_id):
    active_subs = list()
    websites_ids = dbs.db_subscriptions_by_user(tg_id=tg_id)
    for ids in websites_ids:
        ws_name = dbs.db_websites_get_name(ids)
        active_subs.append(ws_name)
    if active_subs:
        active_subs.sort()
        message_list = "\n- "
        message_list += "\n- ".join(active_subs)
        return message_list
    return None


# helper for generating info about a user
def generate_user_data_text(user_data, sanitize=False):
    if sanitize:
        if user_data[1] == 1:
            status_string = "user"
        else:
            status_string = "guest"
    else:
        status_string = "{} ({})".format(user_data[1], status_meaning(user_data[1]))
    message = ("User ID (Telegram ID): " + user_id_linker(str(user_data[0])) + "\n"
               "Status: " + status_string + "\n"
               "First name: " + str(user_data[2]) + "\n"
               "Last name: " + str(user_data[3]) + "\n"
               "Username: " + str(user_data[4]) + "\n")
    if user_data[1] != 0:
        message += ("Name on application: " + str(user_data[5]) + "\n"
                    "Application: " + str(user_data[6]) + "\n"
                    "First interaction: " + str(user_data[7].isoformat(' ', 'seconds')) + "\n")
    subscriptions_list = generate_user_subscriptions_list(user_data[0])
    if subscriptions_list:
        message += "Active subscriptions: " + subscriptions_list
    else:
        message += "Active subscriptions: None"
    return message


# helper for generating info about a website
def generate_website_data_text(website_data, sanitize=False):
    if website_data[4] is not None:
        str_last_time_checked = str(website_data[4].isoformat(' ', 'seconds'))
    else:
        str_last_time_checked = "None"
    if website_data[5] is not None:
        str_last_time_updated = str(website_data[5].isoformat(' ', 'seconds'))
    else:
        str_last_time_updated = "None"
    if website_data[7] is not None:
        str_last_error_time = str(website_data[7].isoformat(' ', 'seconds'))
    else:
        str_last_error_time = "None"
    if sanitize:
        message = ("Name: " + str(website_data[1]) + "\n"
                   "URL: " + str(website_data[2]) + "\n"
                   "Last successful check: " + str_last_time_checked + "\n"
                   "Last successful update: " + str_last_time_updated)
    else:
        message = ("Name: " + str(website_data[1]) + "\n"
                   "Website ID: " + str(website_data[0]) + "\n"
                   "URL: " + str(website_data[2]) + "\n"
                   "Sleep time: " + str(website_data[3]) + "\n"
                   "Last successful check: " + str_last_time_checked + "\n"
                   "Last successful update: " + str_last_time_updated + "\n"
                   "Last error message: " + convert_less_than_greater_than(str(website_data[6])) + "\n"
                   "Last error time: " + str_last_error_time + "\n"
                   "Subscriptions: " + str(dbs.db_subscriptions_by_website(ws_name=website_data[1])) + "\n"
                   "Filters: " + str(unpack_filters(website_data[9])))
    return message


# helper for unpacking the website filter list
def unpack_filters(str_filters):
    if str_filters is not None and str_filters != "":
        list_filters = str_filters.split(",")
    else:
        list_filters = None
    return list_filters


# helper for repacking the website filter list
def repack_filters(list_filters):
    return ",".join(map(str, list_filters))


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
    return "<a href=\"tg://user?id={}\">{}</a>".format(chat_id, chat_id)


###########################################
#    Message-sending wrapper functions    #
###########################################

# edit previously sent message
def send_message_edit(chat_id, message_id, message, reply_markup=None):
    num_this_message = next(num_messages)
    logger.debug("Message #{} (edit of message with ID {}) to {}:\n{}".format(num_this_message, message_id, chat_id, message))
    if not(message):
        logger.warning("Empty message #{} (edit of message with ID {}) to {}. Not sent.".format(num_this_message, message_id, chat_id))
        return
    message = truncate_message(message)
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        logger.debug("Message #{} (edit of message with ID {}) to {} was sent successfully.".format(num_this_message, message_id, chat_id))
    except TelegramError as e:
        exctype, exc, tb = exception_printing(e)
        logger.error("A telegram.{} has occured when trying to send message #{} (edit of message with ID {}) to {}.\nError message: {}\nTraceback:\n{}".format(exctype, num_this_message, message_id, chat_id, exc, tb))
    except Exception as e:
        exctype, exc, tb = exception_printing(e)
        logger.error("A {} has occured when trying to send message #{} (edit of message with ID {}) to {}.\nError message: {}\nTraceback:\n{}".format(exctype, num_this_message, message_id, chat_id, exc, tb))


# reply to a command/input from the user
def send_command_reply(update, context, message, reply_markup=None):
    num_this_message = next(num_messages)
    logger.debug("Message #{} to {}:\n{}".format(num_this_message, update.message.chat_id, message))
    if not(message):
        logger.warning("Empty message #{} to {}. Not sent.".format(num_this_message, update.message.chat_id))
        return
    message = truncate_message(message)
    try:
        context.bot.send_message(chat_id=update.message.chat_id, text=message, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        logger.debug("Message #{} to {} was sent successfully.".format(num_this_message, update.message.chat_id))
    except TelegramError as e:
        exctype, exc, tb = exception_printing(e)
        logger.error("A telegram.{} has occured when trying to send message #{} to {}.\nError message: {}\nTraceback:\n{}".format(exctype, num_this_message, update.message.chat_id, exc, tb))
    except Exception as e:
        exctype, exc, tb = exception_printing(e)
        logger.error("A {} has occured when trying to send message #{} to {}.\nError message: {}\nTraceback:\n{}".format(exctype, num_this_message, update.message.chat_id, exc, tb))


def send_general_broadcast(chat_id, message, reply_markup=None):
    """Send a message to a specified user (not in reply to input)"""
    num_this_message = next(num_messages)
    logger.debug("Message #{} to {}:\n{}".format(num_this_message, chat_id, message))
    if not(message):
        logger.warning("Empty message #{} to {}. Not sent.".format(num_this_message, chat_id))
        return
    message = truncate_message(message)
    try:
        bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
        logger.debug("Message #{} to {} was sent successfully.".format(num_this_message, chat_id))
    except TelegramError as e:
        exctype, exc, tb = exception_printing(e)
        logger.error("A telegram.{} has occured when trying to send message #{} to {}.\nError message: {}\nTraceback:\n{}".format(exctype, num_this_message, chat_id, exc, tb))
    except Exception as e:
        exctype, exc, tb = exception_printing(e)
        logger.error("A {} has occured when trying to send message #{} to {}.\nError message: {}\nTraceback:\n{}".format(exctype, num_this_message, chat_id, exc, tb))


def send_admin_broadcast(message, reply_markup=None):
    """Send a message only to admins (not in reply to input)"""
    admin_message = "[ADMIN BROADCAST]\n" + message
    for adm_chat_id in admin_chat_ids:
        send_general_broadcast(chat_id=adm_chat_id, message=admin_message, reply_markup=reply_markup)


def send_service_message(message, reply_markup=None, chat_id_list=False):
    """Send a message to every (non-denied) account in the database (not in reply to input), unless a specific list of chat IDs is passed.

    Intended as a one-time trigger after substantial changes to the bot.
    """
    service_message = "[SERVICE NOTIFICATION]\n" + message
    if not chat_id_list:
        chat_id_list = dbs.db_users_get_all_ids_with_status(0) + dbs.db_users_get_all_ids_with_status(1) + dbs.db_users_get_all_ids_with_status(2)
    for chat_id in chat_id_list:
        send_general_broadcast(chat_id=chat_id, message=service_message, reply_markup=reply_markup)


# helper for cleanly truncating message bodies that are too long
def truncate_message(message):
    limit = 4096
    warning = "\n... [truncated]"
    if len(message) > limit:
        message = message[:(limit - len(warning))]  # first truncate to limit...
        message = message[:message.rfind(" ")]  # ...and then truncate to last space
        logger.warning("Message too long. Sending only the first {} characters and a [truncated] warning ({} characters in total).".format(len(message), len(message) + len(warning)))
        message += warning
        logger.debug("New, truncated message: {}".format(message))
    return message


###########################################
#              Main function              #
###########################################

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

    # Conversation handlers (need to be added to dispatcher before any other commands in order to make sure cancel fallbacks work) -->
    conversation_handler_apply = ConversationHandler(
        entry_points=[CommandHandler("apply", apply)],
        states={
            STATE_APPLY_NAME: [MessageHandler(Filters.text & (~ Filters.command), apply_name)],
            STATE_APPLY_MESSAGE: [MessageHandler(Filters.text & (~ Filters.command), apply_message)]
        },
        fallbacks=[MessageHandler(Filters.command, cancel)]
    )
    conversation_handler_websites_02_add = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_websites_submenu_01_add_or_request, pattern="webs_01_add_req")],
        states={
            STATE_WEBSITES_02_ADD_REQUEST_NAME: [MessageHandler(Filters.text & (~ Filters.command), helper_websites_submenu_02_add_or_request_name)],
            STATE_WEBSITES_02_ADD_REQUEST_URL: [MessageHandler(Filters.text & (~ Filters.command), helper_websites_submenu_02_add_or_request_url)],
            STATE_WEBSITES_02_ADD_REQUEST_TIME_SLEEP: [MessageHandler(Filters.text & (~ Filters.command), helper_websites_submenu_02_add_or_request_time_sleep)],
        },
        fallbacks=[MessageHandler(Filters.command, cancel)]
    )
    conversation_handler_websites_04_change_attribute = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_websites_submenu_03_change_attribute, pattern="^webs_03_attr-")],
        states={
            STATE_WEBSITES_04_CHANGE_ATTRIBUTE_NAME: [MessageHandler(Filters.text & (~ Filters.command), helper_websites_submenu_04_change_attribute_name)],
            STATE_WEBSITES_04_CHANGE_ATTRIBUTE_URL: [MessageHandler(Filters.text & (~ Filters.command), helper_websites_submenu_04_change_attribute_url)],
            STATE_WEBSITES_04_CHANGE_ATTRIBUTE_TIME_SLEEP: [MessageHandler(Filters.text & (~ Filters.command), helper_websites_submenu_04_change_attribute_time_sleep)],
        },
        fallbacks=[MessageHandler(Filters.command, cancel)]
    )
    conversation_handler_websites_05_change_attribute_filters = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_websites_submenu_04_change_attribute_filters, pattern="^webs_04_attr_filt-")],
        states={
            STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_EXPAND: [MessageHandler(Filters.text & (~ Filters.command), helper_websites_submenu_05_change_attribute_filters_expand)],
            STATE_WEBSITES_05_CHANGE_ATTRIBUTE_FILTERS_OVERWRITE: [MessageHandler(Filters.text & (~ Filters.command), helper_websites_submenu_05_change_attribute_filters_overwrite)],
        },
        fallbacks=[MessageHandler(Filters.command, cancel)]
    )
    # Access levels 0 and 1 -->
    dispatcher.add_handler(conversation_handler_websites_02_add)  # entry point: button callback in /websites (button_websites_submenu_01_add_or_request)
    dispatcher.add_handler(conversation_handler_websites_04_change_attribute)  # entry point: button callback in /websites (button_websites_submenu_03_change_attribute)
    dispatcher.add_handler(conversation_handler_websites_05_change_attribute_filters)  # entry point: button callback in /websites (button_websites_submenu_04_change_attribute_filters)
    # <--
    # Access levels 0 to 3 -->
    # this one needs to be added after the button callback entry points above in order to make /apply a cancel fallback in the /websites conversations
    # the other way around (like here) would be a problem too in theory but /websites is thankfully not a conversation entry point so the /apply conversation can be cancelled normally with /websites (added below)
    dispatcher.add_handler(conversation_handler_apply)  # entry point: /apply
    # <--
    # <--

    # Access levels 0 to 3 -->
    dispatcher.add_handler(CommandHandler("start", start))
    # <--

    # Access levels 0 and 1 -->
    dispatcher.add_handler(CommandHandler("commands", commands))
    dispatcher.add_handler(CommandHandler("subscriptions", subscriptions))
    # Callback helpers for /subscriptions -->
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_info, pattern="^subs_info-"))
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_add, pattern="^subs_add-"))
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_remove, pattern="^subs_rem-"))
    dispatcher.add_handler(CallbackQueryHandler(button_subscriptions_exit, pattern="subs_exit"))
    # <--
    dispatcher.add_handler(CommandHandler("websites", websites))
    # Callback helpers for /websites -->
    dispatcher.add_handler(CallbackQueryHandler(websites, pattern="^webs_00-"))
    dispatcher.add_handler(CallbackQueryHandler(button_websites_submenu_01_detail, pattern="^webs_01_detail-"))
    dispatcher.add_handler(CallbackQueryHandler(button_websites_submenu_02_delete, pattern="^webs_02_del-"))
    dispatcher.add_handler(CallbackQueryHandler(button_websites_submenu_03_delete_confirm, pattern="^webs_03_del-"))
    dispatcher.add_handler(CallbackQueryHandler(button_websites_submenu_02_edit_attributes, pattern="^webs_02_attr-"))
    dispatcher.add_handler(CallbackQueryHandler(button_websites_exit, pattern="webs_exit"))
    # <--
    dispatcher.add_handler(CommandHandler("user", user))
    # Callback helpers for /user -->
    dispatcher.add_handler(CallbackQueryHandler(user, pattern="usr_00"))
    dispatcher.add_handler(CallbackQueryHandler(button_user_submenu_01, pattern="^usr_01-"))
    dispatcher.add_handler(CallbackQueryHandler(button_user_submenu_02, pattern="^usr_02-"))
    dispatcher.add_handler(CallbackQueryHandler(button_user_submenu_03, pattern="^usr_03-"))
    dispatcher.add_handler(CallbackQueryHandler(button_user_exit, pattern="usr_exit"))
    # <--
    dispatcher.add_handler(CommandHandler("stop", stop))
    # <--

    # Only access level 0 -->
    dispatcher.add_handler(CommandHandler("servicenotification", servicenotification))
    # <--

    # Catch-all for unknown commands (any access level) -->
    excluded_commands = [r"\/start", r"\/apply", r"\/commands", r"\/subscriptions", r"\/websites", r"\/user", r"\/stop", r"\/servicenotification"]
    dispatcher.add_handler(MessageHandler(Filters.command & (~ Filters.regex(r"^(" + r"|".join(excluded_commands) + r")$")), unknown_command))
    # <--

    # Handler for errors and exceptions in all bot functions
    dispatcher.add_error_handler(error_callback)

    updater.start_polling()
