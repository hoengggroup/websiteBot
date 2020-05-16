# -*- coding: utf-8 -*-

### python builtins
from datetime import datetime  # for timestamps
import hashlib  # for hashing website content
from os import listdir  # for detecting the rpi dummy file
from os.path import isfile, join, dirname, realpath  # for detecting the rpi dummy file
import platform  # for checking the system we are running on
import random  # for deciding how long to sleep for
import re  # for regex
from signal import signal, SIGABRT, SIGINT, SIGTERM  # for cleanup on exit/termination
import sys  # for errors and terminating
import time  # for sleeping
import traceback  # for logging the full traceback

### external libraries
import html2text  # converting html to text
import sdnotify  # for the systemctl watchdog
from unidecode import unidecode  # for stripping Ümläüte

### our own libraries
from loggerService import create_logger
import dp_edit_distance
import databaseService as dbs
import telegramService as tgs
import requestsService as rqs
import vpnService as vpns


# MAIN PARAMETERS
version_code = "5.1 beta1"
keep_website_history = True


# logging
logger = create_logger("main")

#termination handler
def exit_cleanup(*args):
    disconnection_state = dbs.db_disconnect()
    if not disconnection_state:
        logger.critical("Database did not disconnect successfully.")
    else:
        logger.info("Database disconnected successfully.")
    tgs.send_admin_broadcast("Shutdown complete.")
    tgs.exit_cleanup_tg()
    logger.warning("Shutdown complete. This is the last line.")
    sys.exit(1)

for sig in (SIGABRT, SIGINT, SIGTERM):
    signal(sig, exit_cleanup)


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


def vpn_wait():
    logger.warning("VPN connection could not be validated. Suspending operations until VPN connection is re-validated.")
    retry_counter = 0
    while True:
        alive_notifier.notify("WATCHDOG=1")  # send status: alive
        time.sleep(10)
        if retry_counter < 2:
            if vpns.init(mode="re-establish"):
                logger.info("VPN connection has been re-validated successfully. Back online.")
                retry_counter = 0
                break
        elif retry_counter == 2:
            if vpns.init(mode="re-establish"):
                logger.info("VPN connection has been re-validated successfully. Back online.")
                retry_counter = 0
                break
            else:
                # the first Telegram message after a network change appears to usually time out, so send a dummy message first
                tgs.send_admin_broadcast("This is the first message after the VPN disconnected. Might cause a NetworkError in telegramService.\nDisregard.")
                tgs.send_admin_broadcast("VPN has disconnected, and the connection could not be re-validated immediately. Operations are suspended since disconnecting and until VPN connection is re-established.")
        if retry_counter > 2:
            if vpns.init(mode="re-establish"):
                logger.info("VPN connection has been re-validated successfully. Back online.")
                # the first Telegram message after a network change appears to usually time out, so send a dummy message first
                tgs.send_admin_broadcast("This is the first message after the VPN reconnected. Might cause a NetworkError in telegramService.\nDisregard.")
                tgs.send_admin_broadcast("VPN connection has been re-validated successfully. Back online.")
                retry_counter = 0
                break
        retry_counter += 1


def process_website(logger, current_content, current_ws_name):
    # 1. startup
    logger.debug("Starting processing website.")
    last_time_updated = dbs.db_websites_get_data(ws_name=current_ws_name, field="last_time_updated")
    last_hash = dbs.db_websites_get_data(ws_name=current_ws_name, field="last_hash")
    last_content = dbs.db_websites_get_content(ws_name=current_ws_name, last_time_updated=last_time_updated, last_hash=last_hash)

    # 2. hash website text
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
        current_time_updated = datetime.now()
        dbs.db_websites_set_data(ws_name=current_ws_name, field="last_time_updated", argument=current_time_updated)
        dbs.db_websites_set_data(ws_name=current_ws_name, field="last_hash", argument=current_hash)
        if not keep_website_history:
            dbs.db_websites_delete_content(ws_name=current_ws_name)
        dbs.db_websites_add_content(ws_name=current_ws_name, last_time_updated=current_time_updated, last_hash=current_hash, last_content=current_content)

    # 4. update time last checked
    dbs.db_websites_set_data(ws_name=current_ws_name, field="last_time_checked", argument=datetime.now())
    logger.debug("Finished processing website.")


def main():
    # 1. initialize watchdog
    global alive_notifier
    alive_notifier = sdnotify.SystemdNotifier()
    # Set max_watchdog_time in service to max(time_setup, website_loading_timeout + website_process_time, sleep_time) where:
    #     time_setup = time from here to begin of while loop
    #     website_loading_timeout = timeout setting for loading websites
    #     website_process_time = time it takes to process (changes) of websites (incl. telegram communications)
    #     sleep_time = sleep time at end of while loop

    # 2. initialize database service
    connection_state = dbs.db_connect()
    if not connection_state:
        logger.critical("Fatal error: Could not establish connection with database. Exiting.")
        sys.exit(1)
    else:
        logger.info("Database connected successfully.")

    # 3. detect deployment (check if we are running on rpi)
    dir_path = dirname(realpath(__file__))
    if([f for f in listdir(dir_path) if (isfile(join(dir_path, f)) and f.endswith('.rpi'))] != []):
        on_rpi = True
    else:
        on_rpi = False
    logger.info("Running on RPI: " + str(on_rpi))

    # 4. initialize telegram service
    tgs.init(on_rpi)

    # 5. initialize vpn service
    if on_rpi:
        # @websiteBot_bot
        assert_vpn = True
        vpn_state = vpns.init()
        if not vpn_state:
            logger.critical("Fatal error: Could not validate connection with VPN. Exiting.")
            exit_cleanup()
        else:
            logger.info("VPN connection validated successfully.")
    else:
        # @websiteBotShortTests_bot
        assert_vpn = False

    # 6. inform admins about startup
    tgs.send_admin_broadcast("Starting up.\nVersion: \t"+version_code+"\nPlatform: \t"+str(platform.system())+"\nAssert VPN: \t"+str(assert_vpn)+"\nDeployed: \t"+str(on_rpi))

    # 7. main loop
    try:
        while(True):
            # sleep until VPN connection is re-established if VPN connection is down (if assert_vpn==True)
            if assert_vpn and not vpns.is_vpn_active():
                vpn_wait()

            for ws_id in dbs.db_websites_get_all_ids():
                # notify watchdog
                alive_notifier.notify("WATCHDOG=1")  # send status: alive

                current_ws_name = dbs.db_websites_get_name(ws_id)
                current_url = dbs.db_websites_get_data(ws_name=current_ws_name, field="url")
                current_time = datetime.now()
                elapsed_time = current_time - dbs.db_websites_get_data(ws_name=current_ws_name, field="last_time_checked")

                if elapsed_time.total_seconds() > dbs.db_websites_get_data(ws_name=current_ws_name, field="time_sleep"):
                    logger.debug("Checking website " + str(current_ws_name) + " with url: " + str(current_url))

                    # get website
                    response = rqs.get_url(url=current_url, ws_name=current_ws_name)

                    # process website
                    if not response:
                        logger.warning("Response data is empty for " + str(current_url) + ". Skipping.")
                        continue

                    logger.debug("Extracting content from response data.")
                    current_content = unidecode(html2text.html2text(response.text))
                    process_website(logger, current_content, current_ws_name)

            # notify watchdog
            alive_notifier.notify("WATCHDOG=1")  # send status: alive

            # sleep until next go-around in loop
            # sleep for a random (out of five choices) prime number of seconds so no regular pattern of web requests develops
            choice = random.choice([5, 7, 11, 13, 17])
            logger.debug("Pausing main loop now for " + str(choice) + " seconds.")
            time.sleep(choice)
    except Exception:
        logger.critical("Unknown exception. Exiting.")
        logger.critical("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
        traceback.print_exc()
        tgs.send_admin_broadcast("Unknown exception in main loop.\nExiting.")
        exit_cleanup()


if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    main()
