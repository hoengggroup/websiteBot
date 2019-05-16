# -*- coding: utf-8 -*-

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


def set_webpages_dict_reference(the_webpages_dict_reference):
    global webpages_dict
    webpages_dict = the_webpages_dict_reference


def start(update, context):
    list_webpages = list(webpages_dict.keys())
    message_list = '\n- '
    message_list += '\n- '.join(list_webpages)
    context.bot.send_message(chat_id=update.message.chat_id, text='Welcome. Here is the list of available webpages:', parse_mode='HTML')
    context.bot.send_message(chat_id=update.message.chat_id, text=message_list, parse_mode='HTML')


def subscribe(update, context):
    webpages = list()
    if context.args:
        webpages += list(context.args)
        for wp in webpages:
            if wp in webpages_dict.keys():
                webpage_object = webpages_dict[wp]
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text='Error. Webpage ' + str(wp) + ' does not exist in list.', parse_mode='HTML')
                continue

            if webpage_object.add_chat_id(chat_id_to_add=update.message.chat_id):
                context.bot.send_message(chat_id=update.message.chat_id, text='You have successfully been subscribed to webpage: ' + str(wp), parse_mode='HTML')
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text='Error. Subscription to webpage ' + str(wp) + ' failed or you are already subscribed.', parse_mode='HTML')
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text='Error. You need to specify which website you want to subscribe to.', parse_mode='HTML')


def unsubscribe(update, context):
    webpages = list()
    if context.args:
        webpages += list(context.args)
        for wp in webpages:
            if wp in webpages_dict.keys():
                webpage_object = webpages_dict[wp]
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text='Error. Webpage ' + str(wp) + ' does not exist in list.', parse_mode='HTML')
                continue

            if webpage_object.remove_chat_id(chat_id_to_remove=update.message.chat_id):
                context.bot.send_message(chat_id=update.message.chat_id, text='You have successfully been unsubscribed from webpage: ' + str(wp), parse_mode='HTML')
            else:
                context.bot.send_message(chat_id=update.message.chat_id, text='Error. Unsubscription from webpage ' + str(wp) + ' failed or you are already unsubscribed.', parse_mode='HTML')
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text='Error. You need to specify which website you want to unsubscribe from.', parse_mode='HTML')


def active(update, context):
    webpages = list()
    for wp in list(webpages_dict.keys()):
        webpage_object = webpages_dict[wp]
        if webpage_object.is_chat_id_active(chat_id_to_check=update.message.chat_id):
            webpages.append(wp)

    if webpages:
        # TODO: Make prettier like in "start" function
        context.bot.send_message(chat_id=update.message.chat_id, text='You are currently subscribed to the following webpages: ' + str(webpages), parse_mode='HTML')
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text='Error. Checking subscriptions failed or you are not subscribed to any webpages.', parse_mode='HTML')


def stop(update, context):
    webpages = list(webpages_dict.keys())
    success_message = ''
    fail_message = 0
    for wp in webpages:
        if webpages_dict[wp].remove_chat_id(update.message.chat_id):
            success_message.join(webpages_dict[wp] + ' ')
        else:
            fail_message += 1

    if success_message:
        context.bot.send_message(chat_id=update.message.chat_id, text='You have successfully been unsubscribed from webpages: ' + str(success_message), parse_mode='HTML')
    elif fail_message:
        context.bot.send_message(chat_id=update.message.chat_id, text='Error. Some unsubscriptions failed or you were not subscribed to any webpages.', parse_mode='HTML')


def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text='Sorry, I did not understand that command.', parse_mode='HTML')


def handler(chat_id, message):
    if not(message):
        return
    bot.send_message(chat_id=chat_id, text=message)


webpages_dict = {}

updater = Updater(token='***REMOVED***', use_context=True)
dispatcher = updater.dispatcher
bot = telegram.Bot(token='***REMOVED***')

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('subscribe', subscribe))
dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe))
dispatcher.add_handler(CommandHandler('active', active))
dispatcher.add_handler(CommandHandler('stop', stop))
# The "unknown" handler needs to be added last:
dispatcher.add_handler(MessageHandler(Filters.command, unknown))

updater.start_polling()

# Use this command in the python console to clean up the Telegram service:
# updater.stop()
