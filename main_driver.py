# -*- coding: utf-8 -*-

### python builtins
from datetime import datetime  # for timestamps
import hashlib  # for hashing website content
from os import listdir  # for detecting the rpi dummy file
from os.path import isfile, join, dirname, realpath  # for detecting the rpi dummy file
import platform  # for checking the system we are running on
import random  # for deciding how long to sleep for
from signal import signal, SIGABRT, SIGINT, SIGTERM  # for cleanup on exit/termination
import sys  # for errors and terminating
import time  # for sleeping
import traceback  # for logging the full traceback

### external libraries
import html2text  # for converting html to text
import sdnotify  # for the systemctl watchdog
from unidecode import unidecode  # for stripping Ümläüte

### our own libraries
from configService import version_code, keep_website_history, filter_dict
from loggerService import create_logger
import dp_edit_distance
import databaseService as dbs
import telegramService as tgs
import requestsService as rqs
import vpnService as vpns


# logging
logger = create_logger("main")


#termination handler
signal_caught = False

def exit_cleanup(*args):
    global signal_caught
    if not signal_caught:
        signal_caught = True
        disconnection_state = dbs.db_disconnect()
        if not disconnection_state:
            logger.critical("Database did not disconnect successfully.")
        else:
            logger.info("Database disconnected successfully.")
        tgs.send_admin_broadcast("Shutdown complete.")
        tgs.exit_cleanup_tg()
        logger.info("Telegram bot stopped successfully.")
        logger.warning("Shutdown complete. This is the last line.")
        sys.exit(1)
    else:
        print("KILL SIGNAL IGNORED. WAIT FOR COMPLETION OF TERMINATION ROUTINE.")

for sig in (SIGABRT, SIGINT, SIGTERM):
    signal(sig, exit_cleanup)


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


def process_website(new_content, ws_name, url, last_hash, last_content):
    logger.debug("Started processing website.")

    # 1. hash website text
    new_hash = (hashlib.md5(new_content.encode())).hexdigest()
    logger.debug("Hashes are (new, last): (" + str(new_hash) + ", " + str(last_hash) + ").")

    # 2. if different
    if new_hash != last_hash:
        logger.info("Website hashes do not match. New hash " + str(new_hash) + " vs. last hash " + str(last_hash) + ".")
        logger.debug("Extra check - is content equal: " + str(last_content == new_content) + ".")

        # 2.1 determine difference using DP (O(m * n) ^^)
        logger.debug("dp_edit_distance: Preprocessing #1 - last content.")
        last_words_list = dp_edit_distance.preprocess_content(str(last_content))
        logger.debug("dp_edit_distance: Preprocessing #2 - new content.")
        new_words_list = dp_edit_distance.preprocess_content(str(new_content))
        msg_to_send = "Changes in website <a href=\"" + str(url) + "\">" + str(ws_name) + "</a>:\n\n"

        logger.debug("dp_edit_distance: Calculating edit distance changes.")
        changes = dp_edit_distance.get_edit_distance_changes(last_words_list, new_words_list)

        logger.info("Website word difference is: " + str(changes))
        for change_tupel in changes:
            if change_tupel[0] == "swap":
                msg_to_send += "SWAP: <i>" + tgs.convert_less_than_greater_than(change_tupel[1]) + "</i> TO <b>" + tgs.convert_less_than_greater_than(change_tupel[2]) + "</b>\n"
            elif change_tupel[0] == "added":
                msg_to_send += "ADD: <b>" + tgs.convert_less_than_greater_than(change_tupel[1]) + "</b>\n"
            elif change_tupel[0] == "deleted":
                msg_to_send += "DEL: <i>" + tgs.convert_less_than_greater_than(change_tupel[1]) + "</i>\n"
            else:
                msg_to_send += "Unknown OP: "
                for my_str in change_tupel:
                    msg_to_send += (my_str + " ")
                msg_to_send += "\n"
        
        # 2.2 censor content based on filter list
        filter_hits = list()
        filters = filter_dict.get(ws_name)
        if filters:
            for flt in filters:
                if flt in msg_to_send:
                    filter_hits.append(flt)

        # 2.3 notify world about changes
        user_ids = dbs.db_subscriptions_by_website(ws_name=ws_name)
        # the above database query may return None if the website is deleted in the meantime, so check this explicitly
        if user_ids is None:
            logger.warning("Database query for subscriptions failed for website " + str(ws_name) + ". It was probably deleted from the database since processing started. Aborting processing.")
            return
        else:
            if not filter_hits:
                for ids in user_ids:
                    tgs.send_general_broadcast(ids, msg_to_send)
            else:
                # send censored content only to (subscribed) admins
                subscribed_admin_ids = list(set(user_ids).intersection(tgs.admin_chat_ids))
                for ids in subscribed_admin_ids:
                    tgs.send_general_broadcast(ids, "[CENSORED CONTENT]")
                    tgs.send_general_broadcast(ids, msg_to_send)
                    tgs.send_general_broadcast(ids, "FILTER HITS:")
                    for hit in filter_hits:
                        tgs.send_general_broadcast(ids, hit)

        # 2.4 update values in website table
        new_time_updated = datetime.now()
        if not keep_website_history:
            dbs.db_websites_delete_content(ws_name=ws_name)
        content_success = dbs.db_websites_add_content(ws_name=ws_name, last_time_updated=new_time_updated, last_hash=new_hash, last_content=new_content)
        hash_success = dbs.db_websites_set_data(ws_name=ws_name, field="last_hash", argument=new_hash)
        time_updated_success = dbs.db_websites_set_data(ws_name=ws_name, field="last_time_updated", argument=new_time_updated)
        # the above database interactions may happen after a website has already been deleted, so check if they worked correctly
        if not all([content_success, hash_success, time_updated_success]):
            logger.warning("One or more database updates failed for the changed website " + str(ws_name) + ". It was probably deleted from the database since processing started. Aborting processing.")
            return

    # 3. update time last checked
    # this database interaction may happen after a website has already been deleted, so check if it worked correctly
    if not dbs.db_websites_set_data(ws_name=ws_name, field="last_time_checked", argument=datetime.now()):
        logger.warning("Database update of last_time_checked failed for website " + str(ws_name) + ". It was probably deleted from the database since processing started. Aborting processing.")
        return

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

    # 3. detect deployment
    dir_path = dirname(realpath(__file__))
    if([f for f in listdir(dir_path) if (isfile(join(dir_path, f)) and f.endswith('.websitebot_deployed'))] != []):
        is_deployed = True
    else:
        is_deployed = False
    logger.info("Deployment status: " + str(is_deployed))

    # 4. initialize telegram service
    # @websiteBot_bot if deployed, @websiteBotShortTests_bot if not deployed
    tgs.init(is_deployed)

    # 5. initialize vpn service
    if([f for f in listdir(dir_path) if (isfile(join(dir_path, f)) and f.endswith('.websitebot_assert_vpn'))] != []):
        assert_vpn = True
    else:
        assert_vpn = False
    logger.info("Asserting VPN connection: " + str(assert_vpn))
    if assert_vpn:
        vpn_state = vpns.init()
        if not vpn_state:
            logger.critical("Fatal error: Could not validate connection with VPN. Exiting.")
            exit_cleanup()
        else:
            logger.info("VPN connection validated successfully.")

    # 6. inform admins about startup
    tgs.send_admin_broadcast("Startup complete.\nVersion: \t" + version_code + "\nPlatform: \t" + str(platform.system()) + "\nAsserting VPN: \t" + str(assert_vpn) + "\nDeployed: \t" + str(is_deployed))

    # 7. main loop
    try:
        while(True):
            # sleep until VPN connection is re-established if VPN connection is down (if assert_vpn==True)
            if assert_vpn and not vpns.is_vpn_active():
                vpn_wait()

            for ws_id in dbs.db_websites_get_all_ids():
                # notify watchdog
                alive_notifier.notify("WATCHDOG=1")  # send status: alive

                ws_name = dbs.db_websites_get_name(ws_id)
                last_time_updated = dbs.db_websites_get_data(ws_name=ws_name, field="last_time_updated")
                last_hash = dbs.db_websites_get_data(ws_name=ws_name, field="last_hash")
                last_content = dbs.db_websites_get_content(ws_name=ws_name, last_time_updated=last_time_updated, last_hash=last_hash)
                url = dbs.db_websites_get_data(ws_name=ws_name, field="url")
                last_time_checked = dbs.db_websites_get_data(ws_name=ws_name, field="last_time_checked")
                time_sleep = dbs.db_websites_get_data(ws_name=ws_name, field="time_sleep")
                # any of the seven database interactions above may happen after a website has already been deleted
                # if this is the case, all queries being sent after the deletion will return None as handled by the databaseService
                # so we just need to check if all queries guranteed to be not Null by constraint really returned a value (at least one of the ones we are checking should be the last of the seven of course)
                if not all([ws_name, last_time_updated, url, last_time_checked, time_sleep]):
                    logger.warning("One or more database queries failed for website with ID " + str(ws_id) + ". It was probably deleted from the database since starting the loop. Skipping.")
                    continue
                current_time = datetime.now()
                elapsed_time = current_time - last_time_checked

                if elapsed_time.total_seconds() > time_sleep:
                    logger.debug("Checking website " + str(ws_name) + " with url: " + str(url))

                    # get website
                    response = rqs.get_url(url=url, ws_name=ws_name)

                    # process website
                    if not response:
                        logger.warning("Response data is empty for " + str(url) + ". Skipping.")
                        continue
                    response_stripped = unidecode(html2text.html2text(response.text))
                    process_website(response_stripped, ws_name, url, last_hash, last_content)

            # notify watchdog
            alive_notifier.notify("WATCHDOG=1")  # send status: alive

            # sleep until next go-around in loop
            # sleep for a random (out of five choices) prime number of seconds so no regular pattern of web requests develops
            # choice = random.choice([5, 7, 11, 13, 17])
            choice = 1
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
