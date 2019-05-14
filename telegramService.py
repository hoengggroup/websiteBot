# -*- coding: utf-8 -*-

import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, BaseFilter

'''
class FilterWebpages(BaseFilter):
    def filter(self, message):
        return any(list(main_driver.webpages_dict.keys()) in message.text)
        #return 'Tassilo Test' in message.text
'''

webpages_dict = {}

def set_webpages_dict_reference(the_webpages_dict_reference):
    global webpages_dict
    webpages_dict = the_webpages_dict_reference

def start(update, context):

    list_webpages = list(webpages_dict.keys())
    context.bot.send_message(chat_id=update.message.chat_id, text=list_webpages)


def subscribe(update, context):
    webpage = ' '.join(context.args)
    if(not (webpage in webpages_dict)):
        context.bot.send_message(chat_id=update.message.chat_id, text="Error. Webpage "+str(webpage)+" doesn't exist")
        return

    webpage_object = webpages_dict[webpage]

    if webpage_object.add_chat_id(chat_id_to_add = update.message.chat_id):
        context.bot.send_message(chat_id=update.message.chat_id, text='You have subscribed to webpage: ' + webpage)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text='Error. Subscription failed.')


def stop(update, context):

    webpage = ' '.join(context.args)
    webpage_object = webpages_dict[webpage]
    if webpage_object.remove_chat_id(update.message.chat_id):
        context.bot.send_message(chat_id=update.message.chat_id, text='You have unsubscribed from webpage: ' + webpage)
    else:
        context.bot.send_message(chat_id=update.message.chat_id, text='Error. You were not subscribed.')


def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")


def handler(chat_id, message):
    if(message==""): return
    bot.send_message(chat_id=chat_id, text=message)


updater = Updater(token='***REMOVED***', use_context=True)
dispatcher = updater.dispatcher
bot = telegram.Bot(token= '***REMOVED***')

#filter_webpage = FilterWebpages()

dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('subscribe', subscribe))
dispatcher.add_handler(CommandHandler('stop', stop))

dispatcher.add_handler(MessageHandler(Filters.command, unknown))  # needs to be added last

updater.start_polling()

# updater.stop()
