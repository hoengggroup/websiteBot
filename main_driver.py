#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import hashlib # for hashing website content
import traceback
import html2text # for passing html to text
import requests

import pickle  # to save webpage list
import sdnotify  # for watchdog

import sys
import platform
import time
import datetime
from datetime import date
from random import randint
from pathlib import Path
from unidecode import unidecode  # for stripping Ümläüte

# our own libraries/dependencies
from globalConfig import (version_code, static_ip,static_ip_address,webpage_load_timeout)
from loggerConfig import create_logger_main_driver
import dp_edit_distance
import telegramService
import vpnCheck


webpages_dict = {}
chat_ids_dict = {}


class Webpage:
    def __init__(self, url, t_sleep):
        self.url = url
        self.t_sleep = t_sleep  # sleeping time in seconds
        self.last_time_checked = datetime.datetime.min  # init with minimal datetime value (year 1 AD)
        self.last_time_changed = datetime.datetime.min  # init with minimal datetime value (year 1 AD)
        self.last_error_msg=""

        # to config aka must get/set via methods
        self.chat_ids = set()

        # used while running
        self.last_hash = ""
        self.last_content = ""

    def __str__(self):
        return ("URL: " + str(self.url) + "\n"
                "Sleep timer: " + str(self.t_sleep) + "\n"
                "Last time checked: " + str(self.last_time_checked) + "\n"
                "Last time changed: " + str(self.last_time_changed) + "\n"
                "Last error message: " + str(self.last_error_msg) + "\n"
                "Chat IDs: " + str(self.chat_ids))

    def get_chat_ids(self):
        return self.chat_ids

    def get_url(self):
        return self.url 

    def get_last_hash(self):
        return self.last_hash

    def update_last_content(self, new_last_content):
        new_last_hash = (hashlib.md5(new_last_content.encode())).hexdigest()
        print("new last hash: "+str(new_last_hash))
        if self.last_hash != new_last_hash:
            self.last_time_changed = datetime.datetime.now()
            print("really updated last hash")
        self.last_hash = new_last_hash
        print("updated last hash: "+str(self.get_last_hash()))
        self.last_content = new_last_content

    def get_last_content(self):
        return self.last_content

    def set_t_sleep(self, new_t_sleep):
        self.t_sleep = new_t_sleep
        logger.info("Set new t_sleep for " + str(self.url) + " to: " + str(self.t_sleep))

    def get_t_sleep(self):
        return self.t_sleep

    def update_last_time_checked(self):
        self.last_time_checked = datetime.datetime.now()

    def get_last_time_checked(self):
        return self.last_time_checked

    def is_chat_id_active(self, chat_id_to_check):
        if chat_id_to_check in self.chat_ids:
            return True
        else:
            return False

    def add_chat_id(self, chat_id_to_add):
        if chat_id_to_add in self.chat_ids:
            logger.info("Chat ID " + str(chat_id_to_add) + " is already subscribed to: " + str(self.url))
            return False
        try:
            self.chat_ids.add(chat_id_to_add)
            logger.info("Added chat ID " + str(chat_id_to_add) + " to: " + str(self.url))
            return True
        except KeyError:
            logger.error("Failed to add chat ID " + str(chat_id_to_add) + " to: " + str(self.url))
            return False

    def remove_chat_id(self, chat_id_to_remove):
        if chat_id_to_remove not in self.chat_ids:
            logger.info("Chat ID " + str(chat_id_to_remove) + " is already unsubscribed from: " + str(self.url))
            return False
        try:
            self.chat_ids.remove(chat_id_to_remove)
            logger.info("Removed chat ID " + str(chat_id_to_remove) + " from: " + str(self.url))
            return True
        except KeyError:
            logger.error("Failed to remove chat ID " + str(chat_id_to_remove) + " from: " + str(self.url))
            return False


class ChatID:
    def __init__(self, status, user_data):
        self.status = status  # 0 = admin, 1 = user, 2 = pending, 3 = denied
        self.user_data = None
    
    def get_status(self):
        return self.status
    
    def set_status(self, new_status):
        try:
            self.status = int(new_status)
            return True
        except KeyError:
            logger.error("Failed to set new status " + str(new_status) + " for this chat ID.")
            return False

    def get_user_data(self):
        return self.user_data

    def set_user_data(self, new_user_data):
        try:
            self.user_data = new_user_data
            return True
        except KeyError:
            logger.error("Failed to set new user data " + str(new_user_data) + " for this chat ID.")
            return False


delimiters = "\n", ". "  # delimiters where to split string

# process string ready for dp edit distance
def preprocess_string(str_to_convert):
    # 0. prep delimiters
    regexPattern = '|'.join(map(re.escape, delimiters))  # auto create regex pattern from delimiter list (above)

    # 1. strip all non ascii characters
    str_non_unicode = unidecode(str(str_to_convert))

    # 2. split string @delimiters
    str_split = re.split(regexPattern, str_non_unicode)

    # print("splitted: "+str(str_split))
    # 3. remove empty strings from list as well as string containing only white spaces
    str_list_ret=[]
    for element in str_split:
        if element.isspace() or element == '':
            continue
        str_list_ret.append(element)
    
    return str_list_ret #str_ret


def add_webpage(name, url, t_sleep):
    if name in webpages_dict:
        logger.info("Couldn't add webpage " + name + ", as a webpage with this name already exists.")
        return False
    try:
        new_webpage = Webpage(url=url, t_sleep=t_sleep)
        webpages_dict[name] = new_webpage
        logger.info("Successfully added webpage: " + name + " with url " + str(url) + " and timeout " + str(t_sleep))
        return True
    except Exception as ex:
        logger.error("Couldn't add webpage to webpages_dict. Error: '%s'" % ex.message)  # pylint: disable=no-member
        return False


def remove_webpage(name):
    if name not in webpages_dict:
        logger.info("Couldn't remove webpage " + name + ", as this webpage does not exist.")
        return False
    try:
        del webpages_dict[name]
        logger.info("Successfully removed webpage: " + name)
        return True
    except Exception as ex:
        logger.error("Couldn't remove webpage from webpages_dict. Error: '%s'" % ex.message)  # pylint: disable=no-member
        return False


def create_chat_id(chat_id, status=2, user_data=None):
    if chat_id in chat_ids_dict:
        logger.info("Couldn't add chat ID " + str(chat_id) + ", as this chat ID already exists.")
        return False
    try:
        new_chat_id = ChatID(status=status, user_data=user_data)
        chat_ids_dict[chat_id] = new_chat_id
        logger.info("Successfully added chat ID: " + str(chat_id))
        return True
    except Exception as ex:
        logger.error("Couldn't add chat ID to chat_ids_dict. Error: '%s'" % ex.message)  # pylint: disable=no-member
        return False


def delete_chat_id(chat_id):
    if chat_id not in chat_ids_dict:
        logger.info("Couldn't remove chat ID " + str(chat_id) + ", as this chat ID does not exist.")
        return False
    try:
        del chat_ids_dict[chat_id]
        logger.info("Successfully removed chat ID: " + str(chat_id))
        return True
    except Exception as ex:
        logger.error("Couldn't remove chat ID from chat_ids_dict. Error: '%s'" % ex.message)  # pylint: disable=no-member
        return False


def inf_wait_and_signal():
    logger.warning("[inf sleep] sleeping inf time")
    while True:
        alive_notifier.notify("WATCHDOG=1")  # send status: alive
        time.sleep(10)


def process_webpage(logger,current_text,current_wbpg_dict,current_wbpg_name):
    logger.debug("starting processing webpage")
    current_wbpg=current_wbpg_dict[current_wbpg_name]
    # 2. hash website text
    #current_text+=". abcd. .ef 32r"
    current_hash = (hashlib.md5(current_text.encode())).hexdigest()
    logger.debug("hashes are: current, last: "+str(current_hash)+"\t"+str(current_wbpg.get_last_hash()))
    # 3. if different
    if current_hash != current_wbpg.get_last_hash():
        logger.info("Website hash different. Current: " + str(current_hash) + " vs old hash: " + str(current_wbpg.get_last_hash()))
        logger.debug("Strings equal?" + str(current_wbpg.get_last_content() == current_text))

        # 3.1 determine difference using DP (O(m * n) ^^)
        logger.debug("preprocess 1")
        old_words_list = preprocess_string(current_wbpg.get_last_content())
        logger.debug("preprocess 2")
        new_words_list = preprocess_string(current_text)
        msg_to_send = "CHANGES in " + current_wbpg_name + ":\n"
        
        logger.debug("calling dp edit distance")
        changes = dp_edit_distance.get_edit_distance_changes(old_words_list,new_words_list)

        logger.info("Website word difference is: " + str(changes))
        print("Changes begin ---")
        for change_tupel in changes:
            if change_tupel[0] == "swap":
                msg_to_send += "SWAP: <i>" + change_tupel[1] + "</i> TO <b>" + change_tupel[2] + "</b>\n"
            elif change_tupel[0] == "added":
                msg_to_send += "ADD: <b>" + change_tupel[1] + "</b>\n"
            elif change_tupel[0] == "deleted":
                msg_to_send += "DEL: <i>" + change_tupel[1] + "</i>\n"
            else:
                msg_to_send += "Unknown OP: "
                for my_str in change_tupel:
                    msg_to_send += (my_str + " ")
                msg_to_send += "\n"
        # print(msg_to_send)
        print("--- End of changes. ---")

        # 3.2 notify world about changes
        for current_chat_id in current_wbpg.get_chat_ids():
            telegramService.send_general_broadcast(current_chat_id, msg_to_send)

        # 3.3 update vars of wbpg object
        current_wbpg.update_last_content(current_text)

    # 4. update time last written
    current_wbpg.update_last_time_checked()
    logger.debug("finished processing webpage")                       


def main():
    #-2. init watchdog
    global alive_notifier 
    alive_notifier = sdnotify.SystemdNotifier()
    '''
    max_watchdog_time = max(time_setup, webpage_loading_timeout + webpage_process_time,sleep_time)

    where:
    time_setup = time from here to begin of while loop 
    webpage_loading_timeout = timeout of webdriver when loading webpage
    webpage_process_time = time it takes to process (changes) of a webpage incl. telegram sending
    sleep_time = sleep time at end of while loop
    '''

    #-1. init requests
    

    # 0. init logger
    global logger
    logger = create_logger_main_driver()

    # 1.1 init telegram service
    telegramService.init()
    # send admin msg
    ip_mode_str = "static" if static_ip else "dynamic"
    telegramService.send_admin_broadcast("Starting up.\nVersion: \t"+version_code+"\nPlatform: \t"+str(platform.system())+"\nIP mode: \t"+ip_mode_str)

    # 1.2 init vpn service
    if static_ip:
        vpnCheck.init()
        
        # init and check if configuration is correct
        if static_ip_address == vpnCheck.init():
            # configuration correct
            ip_address = static_ip_address
            pass
        else:
            # wrong static ip set
            logger.error("Startup IP does not match static_ip_address in mode static_ip. Sleeping now inf")
            telegramService.send_admin_broadcast("[IP check] Error on startup. Problem: startup IP does not match static_ip_address in mode static_ip.  Sleeping now inf")
            inf_wait_and_signal()
    else:
        ip_address = vpnCheck.init()


    global webpages_dict
    with open('webpages.pickle', 'rb') as handle:
        webpages_dict = pickle.load(handle)

    global chat_ids_dict
    with open('chatids.pickle', 'rb') as handle:
        chat_ids_dict = pickle.load(handle)


    logger.info("~~~Webpages loading from file START~~~")
    for myKey in webpages_dict:
        myw = webpages_dict[myKey]
        logger.info("Webpage "+myKey + ": " + str(myw))
        #myw.t_sleep = 10
    logger.info("~~~Webpages loading from file END~~~")

    '''
    to add'''
    '''myWebpage = Webpage("http://example.com",15)
    webpages_dict["news"] = myWebpage'''
    '''
    myWebpage = Webpage("https://www.zeit.de/news/index",15)
    webpages_dict["news"] = myWebpage'''

    '''
    myWebpage2 = Webpage("http://reservation.livingscience.ch/wohnen",15)
    webpages_dict["living"] = myWebpage2'''

    
    


    # make objects and functions available / update references in telegramService
    telegramService.set_webpages_dict_reference(webpages_dict)
    telegramService.set_add_webpage_reference(add_webpage)
    telegramService.set_remove_webpage_reference(remove_webpage)
    telegramService.set_chat_ids_dict_reference(chat_ids_dict)
    telegramService.set_create_chat_id_reference(create_chat_id)
    telegramService.set_delete_chat_id_reference(delete_chat_id)


    # set status of pre-configured admin chat IDs to 0 for administrative access after startup
    telegramService.escalate_admin_privileges()


    try:
        while(True):
            # sleep infinitly if VPN connection is down
            if ip_address != vpnCheck.get_ip():
                logger.error("IP address has changed, sleeping now.")
                telegramService.send_admin_broadcast("IP address has changed, sleeping now.")
                inf_wait_and_signal() # sleep inf time

            # webpages_dict_loop = webpages_dict  # so we don't mutate the list (add/remove webpage) while the loop runs
            for current_wbpg_name in list(webpages_dict):
                # notfiy watchdog
                alive_notifier.notify("WATCHDOG=1")  # send status: alive

                try:
                    current_wbpg = webpages_dict[current_wbpg_name]

                    current_time = datetime.datetime.now()
                    elapsed_time = current_time - current_wbpg.get_last_time_checked()

                    if elapsed_time.total_seconds() > current_wbpg.get_t_sleep():
                        logger.debug("Checking website " + current_wbpg_name + " with url: " + current_wbpg.get_url())

                        # 1. get website
                        try:
                            logger.debug("Getting website.")
                            rContent =requests.get(current_wbpg.get_url(),timeout =webpage_load_timeout,verify = False) # TODO: fix SSL support and reset verify to True.
                        except requests.Timeout as e:
                            logger.error("TimeOut Error "+str(e))
                            telegramService.send_admin_broadcast("[getting website] URL: "+str(current_wbpg.get_url())+" Problem: Timeout error "+str(e))
                            current_wbpg.last_error_msg = str(e)
                            continue 
                        except requests.ConnectionError as e:
                            logger.error("Connection Error "+str(e))
                            telegramService.send_admin_broadcast("[getting website] URL: "+str(current_wbpg.get_url())+" Problem: Connection error "+str(e))
                            current_wbpg.last_error_msg = str(e)
                            continue 
                        except:
                            logger.error("An UNKNOWN exception has occured in the get website subroutine.")
                            logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                            telegramService.send_admin_broadcast("[getting website] URL: "+str(current_wbpg.get_url())+" Problem: unknown error")
                            current_wbpg.last_error_msg = str("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                            continue
                        if rContent.status_code != 200:
                            current_error_msg = "Status code is (unequal 0): "+str(rContent.status_code)
                            logger.error(current_error_msg)
                            telegramService.send_admin_broadcast("[getting website] URL: "+str(current_wbpg.get_url())+" Problem: "+current_error_msg)
                            current_wbpg.last_error_msg = current_error_msg
                            continue 

                        # process wbpg
                        logger.debug("getting text")
                        current_text = html2text.html2text(rContent.text)
                        process_webpage(logger,current_text,webpages_dict,current_wbpg_name)
                except RuntimeError as e:
                    logger.error("[website dict iteration] Problem: runtime error "+str(e))
                    telegramService.send_admin_broadcast("[website dict iteration] Problem: runtime error")
                    continue
                except KeyError as e:
                    logger.error("[website dict iteration] Problem: key error "+str(e))
                    telegramService.send_admin_broadcast("[website dict iteration] Problem: key error")
                    continue
            # notfiy watchdog
            alive_notifier.notify("WATCHDOG=1")  # send status: alive

            with open('webpages.pickle', 'wb') as handle:
                pickle.dump(webpages_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
                logger.debug("webpages dict saved.")
            with open('chatids.pickle', 'wb') as handle:
                pickle.dump(chat_ids_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
                logger.debug("chat ids dict saved.")
            # sleep now
            time.sleep(10)

    except Exception:
        logger.error("[MAIN] Problem: unknown exception. Terminating")
        logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
        traceback.print_exc()         
        # send admin msg
        telegramService.send_admin_broadcast("[MAIN] Problem: unknown exception. "+str(sys.exc_info()[0])+" Terminating")
    finally:
        with open('webpages.pickle', 'wb') as handle:
            pickle.dump(webpages_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
            logger.info("webpages dict saved.")
        with open('chatids.pickle', 'wb') as handle:
            pickle.dump(chat_ids_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
            logger.info("chat ids dict saved.")

        telegramService.send_admin_broadcast("[MAIN] shutting down...")
        logger.warning("Shutting down. This is last line.")


if __name__ == "__main__":
   # stuff only to run when not called via 'import' here
   main()