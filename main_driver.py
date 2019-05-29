#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import selenium
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re

import hashlib
import traceback

import pickle  # to save webpage list

import sys
import platform
import time
import datetime
from datetime import date
from random import randint
from pathlib import Path

# our own libraries/dependencies
from loggerConfig import create_logger
import dp_edit_distance
import telegramService

version = "0.3"

logger = create_logger()
parent_directory_binaries = str(Path(__file__).resolve().parents[0])

firefoxOptions = Options()
firefoxOptions.headless = True
firefoxProfile = FirefoxProfile()
firefoxProfile.set_preference("browser.privatebrowsing.autostart", True)  # Enable incognito
firefoxProfile.set_preference("network.cookie.cookieBehavior", 2)  # Disable Cookies
firefoxProfile.set_preference("permissions.default.stylesheet", 2)  # Disable CSS
firefoxProfile.set_preference("permissions.default.image", 2)  # Disable images
firefoxProfile.set_preference("javascript.enabled", False)  # Disable JavaScript
firefoxProfile.set_preference("dom.ipc.plugins.enabled.libflashplayer.so", False)  # Disable Flash
caps = DesiredCapabilities().FIREFOX
# caps["pageLoadStrategy"] = "normal"  # complete
caps["pageLoadStrategy"] = "eager"  # interactive
if platform.system() == "Linux":
    from pyvirtualdisplay import Display
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
    display = Display(visible=0, size=(1024, 768))
    display.start()
    driver = webdriver.Firefox(options=firefoxOptions, desired_capabilities=caps, firefox_profile=firefoxProfile)
else:
    driver = webdriver.Firefox(options=firefoxOptions, desired_capabilities=caps, firefox_profile=firefoxProfile, executable_path=parent_directory_binaries + "/drivers/geckodriver_" + str(platform.system()))
driver.set_page_load_timeout(35)


class Webpage:
    def __init__(self, url, t_sleep):
        self.url = url
        self.t_sleep = t_sleep  # sleeping time in seconds
        self.last_time_checked = datetime.datetime.min  # init with minimal datetime value (year 1 AD)

        # to config aka must get/set via methods
        self.chat_ids = set()

        # used while running
        self.last_hash = ""
        self.last_content = ""

    def get_chat_ids(self):
        return self.chat_ids

    def get_url(self):
        return self.url

    def set_last_hash(self, new_last_hash):
        self.last_hash = new_last_hash

    def get_last_hash(self):
        return self.last_hash

    def set_last_content(self, new_last_content):
        self.last_content = new_last_content

    def get_last_content(self):
        return self.last_content

    def set_t_sleep(self, new_t_sleep):
        self.t_sleep = new_t_sleep
        logger.info("Set new t_sleep for " + str(self.url) + " to: " + str(self.t_sleep))

    def get_t_sleep(self):
        return self.t_sleep

    def set_last_time_checked(self, new_last_time_checked):
        self.last_time_checked = new_last_time_checked

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
            save_websites_dict()
            logger.info("Added chat ID " + str(chat_id_to_add) + " to: " + str(self.url))
            return True
        except KeyError:
            save_websites_dict()
            logger.error("Failed to add chat ID " + str(chat_id_to_add) + " to: " + str(self.url))
            return False

    def remove_chat_id(self, chat_id_to_remove):
        if chat_id_to_remove not in self.chat_ids:
            logger.info("Chat ID " + str(chat_id_to_remove) + " is already unsubscribed from: " + str(self.url))
            return False
        try:
            self.chat_ids.remove(chat_id_to_remove)
            save_websites_dict()
            logger.info("Removed chat ID " + str(chat_id_to_remove) + " from: " + str(self.url))
            return True
        except KeyError:
            save_websites_dict()
            logger.error("Failed to remove chat ID " + str(chat_id_to_remove) + " from: " + str(self.url))
            return False


delimiters = "\n", ". "  # delimiters where to split string
regexPattern = '|'.join(map(re.escape, delimiters))  # auto create regex pattern from delimiter list (above)

from unidecode import unidecode
def remove_non_ascii(text):
    return unidecode(str(text))

def string_to_wordlist(str_to_convert):
    # print("String: " + str_to_convert)
    str_split = re.split(regexPattern, str_to_convert)
    # print("splitted: " + str(str_split))
    return str_split


def save_websites_dict():
    # save back to file
    pickle.dump(webpages_dict, open("save.p", "wb"))


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
        logger.error("Couldn't add webpage to webpages_dict. Error: '%s'" % ex.message)
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
        logger.error("Couldn't remove webpage from webpages_dict. Error: '%s'" % ex.message)
        return False


# 1. load from file
webpages_dict = pickle.load(open("save.p", "rb"))

print("Webpages loaded from file:")
for myKey in webpages_dict:
    myw = webpages_dict[myKey]
    print("Name:"+myKey + ". URL: " + myw.get_url())
    print(type(next(iter(myw.get_chat_ids()), None)))
    print("Chat IDs: " + str(myw.get_chat_ids()))
print("Finished __ webpages loaded from file:")


'''
to add
myWebpage = Webpage("https://google.com",15)
webpages_dict["GoogleMain"] = myWebpage
'''


# make objects and functions available / update references in telegramService
telegramService.set_webpages_dict_reference(webpages_dict)
telegramService.set_add_webpage_reference(add_webpage)
telegramService.set_remove_webpage_reference(remove_webpage)


# send admin msg
telegramService.send_debug("Starting up. Version: "+version+"\nPlatform: "+str(platform.system()))


try:
    while(True):
        webpages_dict_loop = webpages_dict  # so we don't mutate the list (add/remove webpage) while the loop runs
        for current_wpbg_name in list(webpages_dict_loop):
            try:
                current_wbpg = webpages_dict_loop[current_wpbg_name]

                current_time = datetime.datetime.now()
                elapsed_time = current_time - current_wbpg.get_last_time_checked()

                if elapsed_time.total_seconds() > current_wbpg.get_t_sleep():
                    logger.debug("Checking website " + current_wpbg_name + " with url: " + current_wbpg.get_url())

                    # 1. get website
                    try:
                        # open website
                        logger.debug("Getting website.")
                        driver.get(current_wbpg.get_url())
                        logger.debug("Got website.")
                    except selenium.common.exceptions.TimeoutException as e:
                        # logger.error("TimeoutException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                        logger.error("The error is: " + str(e))

                        # bot_sendtext("debug", logger, "TimeoutException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                        # mode = mode_wait_on_net_error
                        continue
                    except selenium.common.exceptions.WebDriverException as e:
                        # logger.error("WebDriverException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                        logger.error("The error is: " + str(e))
                        # bot_sendtext("debug", logger, "WebDriverException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                        # mode = mode_wait_on_net_error
                        continue
                    except:
                        logger.error("An UNKNOWN exception has occured in the get website subroutine.")
                        logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                        # mode = mode_wait_on_net_error
                        telegramService.send_debug("An UNKNOWN exception has occured in the get website subroutine. The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                        continue

                    # 2. hash website text
                    current_text = driver.find_element_by_tag_name("body").text.lower()
                    current_hash = (hashlib.md5(current_text.encode())).hexdigest()

                    # 3. if different
                    if current_hash != current_wbpg.get_last_hash():
                        logger.info("Website hash different. Current: " + str(current_hash) + " vs old hash: " + str(current_wbpg.last_hash))
                        print("Strings equal?" + str(current_wbpg.get_last_content() == current_text))

                        # 3.1 determine difference using DP (O(m * n) ^^)
                        old_words_list = string_to_wordlist(current_wbpg.get_last_content())
                        new_words_list = string_to_wordlist(current_text)

                        msg_to_send = "CHANGES in " + current_wpbg_name + ":\n"
                        changes = dp_edit_distance.get_edit_distance_changes(old_words_list, new_words_list)
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
                        msg_to_send = remove_non_ascii(msg_to_send)
                        print(msg_to_send)
                        print("--- End of changes. ---")

                        # 3.2 notify world about changes
                        # TODO
                        for current_chat_id in current_wbpg.get_chat_ids():
                            telegramService.handler(current_chat_id, msg_to_send)
                        # - iterate over list of chat ids and send message to them

                        # 3.3 update vars of wbpg object
                        current_wbpg.set_last_hash(current_hash)
                        current_wbpg.set_last_content(current_text)

                    # 4. update time last written
                    current_wbpg.set_last_time_checked(datetime.datetime.now())
            except RuntimeError:
                logger.error("Runtime error: dict problem runtime")
                continue
            except KeyError:
                logger.error("Runtime error: dict problem key not existent")
                continue
        # save back to file
        pickle.dump(webpages_dict_loop, open("save.p", "wb"))

        # sleep now
        time.sleep(10)
except Exception as ex:
    logger.error("An UNKNOWN exception has occured in main.")
    logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
    traceback.print_exc()         
    # send admin msg
    telegramService.send_debug("An UNKNOWN exception has occured in main." )


print("eof")
