#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### python builtins
from datetime import datetime  # for timestamps
import hashlib  # for hashing website content
import html2text  # for passing html to text
import platform  # for checking the system we are running on
import random  # for deciding how long to sleep for
import re  # for regex
import requests  # for internet traffic
import sys  # for errors and terminating
import time  # for sleeping
import traceback  # for logging the full traceback

### external libraries
import sdnotify  # for the watchdog
from unidecode import unidecode  # for stripping Ümläüte

### our own libraries
from loggerConfig import create_logger
import dp_edit_distance
import databaseService as dbs
import telegramService as tgs
import vpnCheck as vpns
#TODO: from sendPushbullet import send_push


version_code = "5.0 alpha3"
website_load_timeout = 10

# logging
global logger
logger = create_logger("main")


# process string ready for dp_edit_distance
def preprocess_string(str_to_convert):
    # 0. prepare delimiters
    delimiters = "\n", ". "  # delimiters where to split string
    regexPattern = '|'.join(map(re.escape, delimiters))  # auto create regex pattern from delimiter list

    # 1. strip all non-ascii characters
    str_non_unicode = unidecode(str(str_to_convert))

    # 2. split string at delimiters
    str_split = re.split(regexPattern, str_non_unicode)

    # 3. remove empty strings from list as well as string containing only white spaces
    str_list_ret = []
    for element in str_split:
        if element.isspace() or element == '':
            continue
        str_list_ret.append(element)

    return str_list_ret


def vpn_wait(checking):
    logger.warning("Suspending operations until VPN connection is re-established.")
    while True:
        alive_notifier.notify("WATCHDOG=1")  # send status: alive
        time.sleep(10)
        if checking:
            if vpns.init(mode="re-establish"):
                logger.info("VPN connection has been re-established successfully. Back online.")
                # the first Telegram message after a network change appears to always time out, so send a dummy message before actually starting back up
                tgs.send_admin_broadcast("This is the first message after the VPN reconnected. Usually causes a NetworkError because of a timeout due to the changed connection.\nDisregard.")
                tgs.send_admin_broadcast("VPN connection has been re-established successfully. Back online.")
                break


def process_website(logger, current_content, current_ws_name):
    # 1. startup
    logger.debug("Starting processing website.")
    last_hash = dbs.db_websites_get_data(ws_name=current_ws_name, field="last_hash")
    last_content = dbs.db_websites_get_data(ws_name=current_ws_name, field="last_content")

    # 2. hash website text
    # current_text+=". abcd. .ef 32r"
    current_hash = (hashlib.md5(current_content.encode())).hexdigest()
    logger.debug("Hashes are (current, last): (" + str(current_hash) + ", " + str(last_hash) + ").")
    # 3. if different
    if current_hash != last_hash:
        logger.info("Website hashes do not match. Current hash " + str(current_hash) + " vs. previous hash " + str(last_hash) + ".")
        logger.debug("Content equal? " + str(last_content == current_content) + ".")

        # 3.1 determine difference using DP (O(m * n) ^^)
        logger.debug("Preprocess 1.")
        old_words_list = preprocess_string(last_content)
        logger.debug("Preprocess 2.")
        new_words_list = preprocess_string(current_content)
        link_to_current_ws = dbs.db_websites_get_data(ws_name=current_ws_name, field="url")
        msg_to_send = "Changes in website <a href=\"" + str(link_to_current_ws) + "\">" + str(current_ws_name) + "</a>:\n\n"

        logger.debug("Calling dp_edit_distance.")
        changes = dp_edit_distance.get_edit_distance_changes(old_words_list, new_words_list)

        logger.info("Website word difference is: " + str(changes))
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

        # 3.2 notify world about changes
        user_ids = dbs.db_subscriptions_by_website(ws_name=current_ws_name)
        for ids in user_ids:
            tgs.send_general_broadcast(ids, msg_to_send)

        # 3.3 update values in website table
        dbs.db_websites_set_data(ws_name=current_ws_name, field="last_time_updated", argument=datetime.now())
        dbs.db_websites_set_data(ws_name=current_ws_name, field="last_hash", argument=current_hash)
        dbs.db_websites_set_data(ws_name=current_ws_name, field="last_content", argument=current_content)

    # 4. update time last checked
    dbs.db_websites_set_data(ws_name=current_ws_name, field="last_time_checked", argument=datetime.now())
    logger.debug("Finished processing website.")


def main():
    # 1. initialize watchdog
    global alive_notifier
    alive_notifier = sdnotify.SystemdNotifier()
    ''' max_watchdog_time = max(time_setup, website_loading_timeout + website_process_time, sleep_time)
    where:
    time_setup = time from here to begin of while loop
    website_loading_timeout = timeout of webdriver when loading website
    website_process_time = time it takes to process (changes) of a website incl. telegram sending
    sleep_time = sleep time at end of while loop '''

    # 2. initialize database service
    connection_state = dbs.db_connect()
    if not connection_state:
        logger.critical("Fatal error: Could not establish connection with database. Terminating.")
        sys.exit()
    else:
        logger.info("Database connected successfully.")

    # 3. initialize telegram service
    tgs.init()

    # 4. initialize vpn service
    if platform.system() == "Linux":
        # @websiteBot_bot
        assert_vpn = True
        vpn_state = vpns.init()
        if not vpn_state:
            logger.critical("Fatal error: Could not validate connection with VPN. Terminating.")
            sys.exit()
        else:
            logger.info("VPN connection validated successfully.")
    else:
        # @websiteBotShortTests_bot
        assert_vpn = False

    # 5. inform admins about startup
    assert_vpn_str = "True" if assert_vpn else "False"
    tgs.send_admin_broadcast("Starting up.\nVersion: \t"+version_code+"\nPlatform: \t"+str(platform.system())+"\nAssert VPN: \t"+assert_vpn_str)
    #TODO: send_push("System","Starting up "+str(version_code))

    # 6. main loop
    try:
        while(True):
            # sleep until VPN connection is re-established if VPN connection is down (if assert_vpn==True)
            if assert_vpn and not vpns.is_vpn_active():
                logger.warning("VPN status has changed, suspending operations until VPN connection is re-established.")
                # the first Telegram message after a network change appears to always time out, so send a dummy message before actually starting the re-connection checker
                tgs.send_admin_broadcast("This is the first message after the VPN disconnected. Usually causes a NetworkError because of a timeout due to the changed connection.\nDisregard.")
                tgs.send_admin_broadcast("VPN status has changed, suspending operations until VPN connection is re-established.")
                #TODO: send_push("System","VPN status has changed, suspending operations until VPN connection is re-established.")
                vpn_wait(checking=True)

            for ws_id in dbs.db_websites_get_all_ids():
                # notify watchdog
                alive_notifier.notify("WATCHDOG=1")  # send status: alive

                try:
                    current_ws_name = dbs.db_websites_get_name(ws_id)
                    current_url = dbs.db_websites_get_data(ws_name=current_ws_name, field="url")
                    current_time = datetime.now()
                    elapsed_time = current_time - dbs.db_websites_get_data(ws_name=current_ws_name, field="last_time_checked")

                    if elapsed_time.total_seconds() > dbs.db_websites_get_data(ws_name=current_ws_name, field="time_sleep"):
                        logger.debug("Checking website " + str(current_ws_name) + " with url: " + str(current_url))

                        # get website
                        try:
                            logger.debug("Getting website.")
                            rContent = requests.get(current_url, timeout=website_load_timeout, verify=False)  # TODO: fix SSL support and reset verify to True.
                        except requests.Timeout as e:
                            logger.error("Timeout Error: "+str(e))
                            tgs.send_admin_broadcast("[MAIN] URL: "+str(current_url)+" Problem: Timeout error "+str(e))
                            dbs.db_websites_set_data(ws_name=current_ws_name, field="last_error_msg", argument=str(e))
                            dbs.db_websites_set_data(ws_name=current_ws_name, field="last_error_time", argument=datetime.now())
                            continue
                        except requests.ConnectionError as e:
                            logger.error("Connection Error: "+str(e))
                            tgs.send_admin_broadcast("[MAIN] URL: "+str(current_url)+" Problem: Connection error "+str(e))
                            dbs.db_websites_set_data(ws_name=current_ws_name, field="last_error_msg", argument=str(e))
                            dbs.db_websites_set_data(ws_name=current_ws_name, field="last_error_time", argument=datetime.now())
                            continue
                        except Exception:
                            logger.error("An UNKNOWN exception has occured while trying to fetch the website with URL:" + str(current_url))
                            logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                            tgs.send_admin_broadcast("[MAIN] URL: " + str(current_url) + " Problem: Unknown error.")
                            error_msg = str("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                            dbs.db_websites_set_data(ws_name=current_ws_name, field="last_error_msg", argument=error_msg)
                            dbs.db_websites_set_data(ws_name=current_ws_name, field="last_error_time", argument=datetime.now())
                            continue
                        if rContent.status_code != 200:
                            error_msg = "Status code is (unequal 200): " + str(rContent.status_code)
                            logger.error(error_msg)
                            tgs.send_admin_broadcast("[MAIN] URL: " + str(current_url) + " Problem: " + error_msg)
                            dbs.db_websites_set_data(ws_name=current_ws_name, field="last_error_msg", argument=error_msg)
                            dbs.db_websites_set_data(ws_name=current_ws_name, field="last_error_time", argument=datetime.now())
                            continue

                        # process website
                        logger.debug("Getting content.")
                        current_content = html2text.html2text(rContent.text)
                        process_website(logger, current_content, current_ws_name)
                except RuntimeError as e:
                    logger.error("Runtime error: " + str(e))
                    tgs.send_admin_broadcast("[MAIN] Runtime error.")
                    continue

            # notify watchdog
            alive_notifier.notify("WATCHDOG=1")  # send status: alive

            # sleep until next go-around in loop
            # sleep for a random (out of five choices) prime number of seconds so no regular pattern of web requests develops
            choice = random.choice([5, 7, 11, 13, 17])
            logger.debug("Pausing main loop now for " + str(choice) + " seconds.")
            time.sleep(choice)

    except Exception:
        logger.critical("Unknown exception. Terminating")
        logger.critical("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
        traceback.print_exc()
        tgs.send_admin_broadcast("[MAIN] Unknown exception.\n" + str(sys.exc_info()[0]) + "\nTerminating.")
    finally:
        disconnection_state = dbs.db_disconnect()
        if not disconnection_state:
            logger.critical("Database did not disconnect successfully.")
        else:
            logger.info("Database disconnected successfully.")

        tgs.send_admin_broadcast("Shutting down...")
        logger.warning("Shutting down. This is the last line.")


if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    main()
