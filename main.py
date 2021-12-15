# -*- coding: utf-8 -*-

# PYTHON BUILTINS
from os import listdir  # for detecting the rpi dummy file
from os.path import isfile, join, dirname, realpath  # for detecting the rpi dummy file
import platform  # for checking the system we are running on
from signal import signal, SIGABRT, SIGINT, SIGTERM  # for cleanup on exit/termination
import sys  # for os interaction and terminating
import traceback  # for logging the full traceback

# EXTERNAL LIBRARIES
import sdnotify  # for the systemctl watchdog

# OUR OWN LIBRARIES
from module_config import version_code
from module_logging import create_logger
import module_driver as drv
import module_database as dbs
import module_telegram as tgs
import module_vpn as vpns


# logging
logger = create_logger("main")


# termination handler
signal_caught = False
signal_on_exception = False


def exit_cleanup(*args):
    global signal_caught
    if not signal_caught:
        signal_caught = True
        if signal_on_exception:
            logger.warning("Kill signal received because of an exception. Starting cleanup and shutting down.")
        else:
            logger.warning("Kill signal received. Starting cleanup and shutting down.")
        db_disconnection_state = dbs.db_disconnect()
        if not db_disconnection_state:
            logger.critical("Database did not disconnect successfully.")
        else:
            logger.info("Database disconnected successfully.")
        tgs.send_admin_broadcast("Shutdown in progress. This is the last Telegram message.")
        tg_disconnection_state = tgs.exit_cleanup_tg()
        if not tg_disconnection_state:
            logger.critical("Telegram bot did not stop successfully.")
        else:
            logger.info("Telegram bot stopped successfully.")
        logger.warning("Shutdown complete. This is the last line.")
        if db_disconnection_state and tg_disconnection_state and not signal_on_exception:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print("\nKILL SIGNAL IGNORED. WAIT FOR COMPLETION OF TERMINATION ROUTINE.")


for sig in (SIGABRT, SIGINT, SIGTERM):
    signal(sig, exit_cleanup)


# systemctl watchdog
alive_notifier = sdnotify.SystemdNotifier()
# Set max_watchdog_time in service to max(time_setup, website_loading_timeout + website_process_time, sleep_time) where:
#     time_setup = time from here to begin of while loop
#     website_loading_timeout = timeout setting for loading websites
#     website_process_time = time it takes to process (changes) of websites (incl. telegram communications)
#     sleep_time = sleep time at end of while loop


def main():
    # 1. initialize database service
    connection_state = dbs.db_connect()
    if not connection_state:
        logger.critical("Fatal error: Could not establish connection with database. Exiting.")
        sys.exit(1)
    else:
        logger.info("Database connected successfully.")

    # 2. detect deployment
    dir_path = dirname(realpath(__file__))
    if([f for f in listdir(dir_path) if (isfile(join(dir_path, f)) and f.endswith('.websitebot_deployed'))] != []):
        is_deployed = True
    else:
        is_deployed = False
    logger.info("Deployment status: {}".format(is_deployed))

    # 3. initialize telegram service
    # @websiteBot_bot if deployed, @websiteBotShortTests_bot if not deployed
    tgs.init(is_deployed)

    # 4. initialize vpn service
    if([f for f in listdir(dir_path) if (isfile(join(dir_path, f)) and f.endswith('.websitebot_assert_vpn'))] != []):
        assert_vpn = True
    else:
        assert_vpn = False
    logger.info("Asserting VPN connection: {}".format(assert_vpn))
    if assert_vpn:
        vpn_state = vpns.init()
        if not vpn_state:
            logger.critical("Fatal error: Could not validate connection with VPN. Exiting.")
            exit_cleanup()
        else:
            logger.info("VPN connection validated successfully.")

    # 5. inform admins about startup
    tgs.send_admin_broadcast("Startup complete.\nVersion: \t{}\nPlatform: \t{}\nAsserting VPN: \t{}\nDeployed: \t{}".format(version_code, platform.system(), assert_vpn, is_deployed))

    # 6. main loop
    try:
        while(True):
            drv.driver_loop(alive_notifier, assert_vpn)
    except Exception as exc:
        exctype = type(exc).__name__
        tb = "\n".join(traceback.format_tb(exc.__traceback__))
        logger.critical("A {} has occured in the main script. Exiting.\nError message: {}\nTraceback:\n{}".format(exctype, exc, tb))
        tgs.send_admin_broadcast("A {} has occured in the main script. Exiting.\nError message: {}\nTraceback:\n{}".format(exctype, tgs.convert_less_than_greater_than(exc), tgs.convert_less_than_greater_than(tb)))
        global signal_on_exception
        signal_on_exception = True
        exit_cleanup()


if __name__ == "__main__":
    # stuff only to run when not called via 'import' here
    main()
