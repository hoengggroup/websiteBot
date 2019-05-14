#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import selenium
from selenium import webdriver
import hashlib

import time
import datetime
from datetime import date
import sys
from random import randint
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pathlib import Path
import pickle # to save webpage list

# our dependecies
from loggerConfig import create_logger
import dp_edit_distance
import telegramService


logger = create_logger()

firefox = False

parent_directory_binaries = str(Path(__file__).resolve().parents[0])

if firefox:
    firefoxProfile = FirefoxProfile()
    firefoxProfile.set_preference("browser.privatebrowsing.autostart", True)
    # Disable CSS
    firefoxProfile.set_preference('permissions.default.stylesheet', 2)
    # Disable images
    firefoxProfile.set_preference('permissions.default.image', 2)
    # Disable JavaScript
    firefoxProfile.set_preference('javascript.enabled', False)
    # Disable Flash
    firefoxProfile.set_preference('dom.ipc.plugins.enabled.libflashplayer.so', 'false')
    print("hi")
    caps = DesiredCapabilities().FIREFOX
    # caps["pageLoadStrategy"] = "normal"  # complete
    caps["pageLoadStrategy"] = "eager"  # interactive

    driver = webdriver.Firefox(desired_capabilities=caps, executable_path=parent_directory_binaries + '/drivers/geckodriver_mac', firefox_profile=firefoxProfile)
    driver.set_page_load_timeout(5)
else:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(executable_path=parent_directory_binaries + '/drivers/chromedriver_mac', options=chrome_options)


class Webpage:

    def __init__(self, url, t_sleep):
        self.url = url
        self.t_sleep = t_sleep # sleeping time in seconds
        self.last_time_checked = datetime.datetime(1999, 2, 28, 23, 23, 53, 952623) # init with very old value

        # to config aka must get/set via methods
        self.chat_ids = set()

        # used while running
        self.last_hash = ""
        self.last_content = ""
    
    def get_chat_ids(self):
        return self.chat_ids
    
    def get_url(self):
        return self.url

    def set_last_hash(self,new_last_hash):
        self.last_hash = new_last_hash
    
    def get_last_hash(self):
        return self.last_hash

    def set_last_content(self,new_last_content):
        self.last_content = new_last_content
    
    def get_last_content(self):
        return self.last_content
    
    def set_t_sleep(self, new_t_sleep):
        self.t_sleep = new_t_sleep
        logger.info("Set new t_sleep for "+str(self.url) +" to "+str(self.t_sleep))

    def get_t_sleep(self):
        return self.t_sleep

    def set_last_time_checked(self,new_last_time_checked):
        self.last_time_checked = new_last_time_checked
    
    def get_last_time_checked(self):
        return self.last_time_checked

    def add_chat_id(self, chat_id_to_add):
        try:
            self.chat_ids.add(chat_id_to_add)
            safe_websites_dict()
            logger.info("Added chat ID "+str(chat_id_to_add) +" to "+str(self.url))
            return True
        except KeyError:
            safe_websites_dict()
            logger.info("Failed to add chat ID "+str(chat_id_to_add) +" to "+str(self.url))
            return False
    

    def remove_chat_id(self, chat_id_to_remove):
        try:
            self.chat_ids.remove(chat_id_to_remove)
            safe_websites_dict()
            logger.info("Removed chat ID "+str(chat_id_to_remove) +" from "+str(self.url))
            return True
        except KeyError:
            safe_websites_dict()
            logger.info("Failed to remove chat ID "+str(chat_id_to_remove) +" from "+str(self.url))
            return False

    

def string_to_wordlist(str_to_convert):
    my_ret = []
    for word in str_to_convert.split():
        my_ret.append(word)
    return my_ret

def safe_websites_dict():
    # save back to file
    pickle.dump(webpages_dict,open("save.p","wb"))

# 1. load from file
webpages_dict = pickle.load(open("save.p","rb"))


print("Webpages loaded from file:")
for myKey in webpages_dict:
    myw = webpages_dict[myKey]
    print(myKey+": "+ myw.get_url())
    print(type(next(iter(myw.get_chat_ids()), None)))
    print("Chat IDs: "+str(myw.get_chat_ids()))
print("Finished __ webpages loaded from file:")


'''
to add
myWebpage = Webpage("https://google.com",15)
webpages_dict["GoogleMain"] = myWebpage'''



# update reference in telegramService
telegramService.set_webpages_dict_reference(webpages_dict)



while(True):
    for current_wpbg_name in webpages_dict:

        current_wbpg = webpages_dict[current_wpbg_name]

        current_time = datetime.datetime.now()
        elapsed_time = current_time - current_wbpg.get_last_time_checked()

        if(elapsed_time.total_seconds() > current_wbpg.get_t_sleep()):
            logger.debug("checking website " + current_wpbg_name+" with url "+current_wbpg.get_url()+". ")

            # 1. get website
            try:
                # open website
                logger.debug("Getting website")
                driver.get(current_wbpg.get_url())
                logger.debug("Got website")
            except selenium.common.exceptions.TimeoutException as e:
                #logger.error("TimeoutException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                #bot_sendtext("debug", logger, "TimeoutException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                #mode = mode_wait_on_net_error
                continue
            except selenium.common.exceptions.WebDriverException as e:
                #logger.error("WebDriverException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                # bot_sendtext("debug", logger, "WebDriverException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                #mode = mode_wait_on_net_error
                continue
            except:
                logger.error("An UNKNOWN exception has occured in the get website subroutine.")
                logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                #mode = mode_wait_on_net_error
                continue

            # 2. hash website text
            current_text =  driver.find_element_by_tag_name("body").text
            current_hash = (hashlib.md5(current_text.encode())).hexdigest()

            # 3. if different:
            if(current_hash != current_wbpg.get_last_hash()):
                logger.info("Website hash different. Current: "+str(current_hash)+" vs old hash: "+str(current_wbpg.last_hash))
                print("Strings equal?"+str(current_wbpg.get_last_content() == current_text))
                # 3.1 determine difference using DP (O(m * n) ^^)
                old_words_list = string_to_wordlist(current_wbpg.get_last_content())
                new_words_list = string_to_wordlist(current_text)

                msg_to_send=""
                changes = dp_edit_distance.get_edit_distance_changes(old_words_list, new_words_list)
                logger.info("Website word difference is: "+str(changes))
                print("Changes begin ---")
                for change_tupel in changes:
                    for my_str in change_tupel:
                        print(str(my_str), end=' ')
                        msg_to_send += (my_str+" ")
                    print()
                    msg_to_send += "\n"
                print("--- End of changes. ---")

                # 3.2 notify world about changes
                # TODO
                for current_chat_id in current_wbpg.get_chat_ids():
                    telegramService.handler(current_chat_id,msg_to_send)
                # - iterate over list of chat ids and send message to them

                # 3.3 update vars of wbpg object
                current_wbpg.set_last_hash(current_hash)
                current_wbpg.set_last_content(current_text)

            # 4. update time last written
            current_wbpg.set_last_time_checked (datetime.datetime.now())

    # save back to file
    pickle.dump(webpages_dict,open("save.p","wb"))

    # sleep now
    time.sleep(10)





print("eof")

