#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import selenium
from selenium import webdriver

import time
import sys
from random import randint
from pathlib import Path

from sendTelegram import bot_sendtext
from loggerConfig import create_logger
from vpnCheck import vpn_check
from globalConfig import (version_code, device_type, debugging_enabled,
                          debug_loop_counter, debug_loop_limit,
                          debug_local_URL, mode_normal, mode_wait_on_net_error)
from websiteConfig_1 import (website_URL, alive_signal_threshold,
                             min_sleep_time, max_sleep_time,
                             sleep_time_on_network_error,
                             sleep_counter_due_to_network_error,
                             check_livingscience)


logger = create_logger()
parent_directory_binaries = str(Path(__file__).resolve().parents[0])


# specify imports and selenium drivers for various devices
if device_type == "RPI":
    from pyvirtualdisplay import Display
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

    display = Display(visible=0, size=(1024, 768))
    display.start()

    firefoxProfile = FirefoxProfile()
    firefoxProfile.set_preference("browser.privatebrowsing.autostart", True)
    firefoxProfile.set_preference("http.response.timeout", 5)
    firefoxProfile.set_preference("dom.max_script_run_time", 5)
    driver = webdriver.Firefox(firefox_profile=firefoxProfile)
    driver.set_page_load_timeout(5)

    from sendPushbullet import send_push
    send_push("Start", "System just started.")

elif device_type == "manual_firefox_mac" or device_type == "manual_firefox_win":
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

    firefoxProfile = FirefoxProfile()
    firefoxProfile.set_preference("browser.privatebrowsing.autostart", True)

    if device_type == "manual_firefox_mac":
        driver = webdriver.Firefox(executable_path=parent_directory_binaries + '/drivers/geckodriver_mac', firefox_profile=firefoxProfile)

    elif device_type == "manual_firefox_win":
        driver = webdriver.Firefox(executable_path=parent_directory_binaries + '/drivers/geckodriver_win.exe', firefox_profile=firefoxProfile)

elif device_type == "manual_chrome_mac":
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(executable_path=parent_directory_binaries + '/drivers/chromedriver_mac', options=chrome_options)

else:
    logger.error("Invalid device type. Exiting.")
    sys.exit()


# startup; initial IP/VPN status check
logger.info("Starting up. Current version is: " + version_code + " Device is: " + device_type)
bot_sendtext("debug", logger, "Starting up.\nCurrent version is: " + version_code + "\nDevice is: " + device_type)
last_alive_signal_time = int(time.time())
ip_address, mode = vpn_check(logger, True, "0.0.0.0", mode_normal)


# main loop
try:
    while True:
        if mode == mode_normal:
            logger.debug("Waking up from sleep. Normal mode.")
            # test with local saved webpage when debugging
            if debugging_enabled:
                debug_loop_counter += 1
                if debug_loop_counter == debug_loop_limit:
                    website_URL = debug_local_URL

            # subsequent IP/VPN status check
            ip_address, mode = vpn_check(logger, False, ip_address, mode)
            if mode != mode_normal or ip_address == "0.0.0.0":
                continue

            try:
                # open website
                logger.debug("Getting website")
                driver.get(website_URL)
                logger.debug("Got website")
            except selenium.common.exceptions.TimeoutException as e:
                logger.error("TimeoutException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                bot_sendtext("debug", logger, "TimeoutException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                mode = mode_wait_on_net_error
                continue
            except selenium.common.exceptions.WebDriverException as e:
                logger.error("WebDriverException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                bot_sendtext("debug", logger, "WebDriverException has occured in the get website subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                mode = mode_wait_on_net_error
                continue
            except:
                logger.error("An UNKNOWN exception has occured in the get website subroutine.")
                logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                mode = mode_wait_on_net_error
                continue

            try:
                rowWhgnr_field, mode = check_livingscience(driver, logger, mode)

            except selenium.common.exceptions.TimeoutException as e:
                logger.error("TimeoutException has occured in the row whgnr retreival subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                bot_sendtext("debug", logger, "TimeoutException has occured in the row whgnr retreival subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                mode = mode_wait_on_net_error
                continue

            except selenium.common.exceptions.WebDriverException as e:
                logger.error("WebDriverException has occured in the row whgnr retreival subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                bot_sendtext("debug", logger, "WebDriverException has occured in the row whgnr retreival subroutine. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
                mode = mode_wait_on_net_error
                continue

            except:
                logger.error("An UNKNOWN exception has occured in the row whgnr subroutine.")
                logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                mode = mode_wait_on_net_error
                continue

            # alive signal maintainer
            if int(time.time()) - last_alive_signal_time > alive_signal_threshold:
                logger.debug("Still alive #slErrCo: " + str(sleep_counter_due_to_network_error))
                bot_sendtext("debug", logger, "Still alive. #slErrCo: " + str(sleep_counter_due_to_network_error))
                last_alive_signal_time = int(time.time())
                sleep_counter_due_to_network_error = 0

            # sleeping
            sleep_time = randint(min_sleep_time, max_sleep_time)
            logger.debug("Sleeping for " + str(sleep_time) + " seconds.")
            time.sleep(sleep_time)

        elif mode == mode_wait_on_net_error:
            logger.info("Sleeping now in NET ERROR mode.")
            time.sleep(sleep_time_on_network_error)
            sleep_counter_due_to_network_error += 1
            logger.info("Woke up from NET ERROR mode sleep.")
            mode = mode_normal

        else:
            logger.error("UNKNOWN MODE")
            bot_sendtext("debug", logger, "Error: Unknown mode. Entering MODE ON NET ERROR.")
            mode = mode_wait_on_net_error

except:
    logger.error("An UNKNOWN exception has occured in the main loop.")
    logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
    bot_sendtext("debug", logger, "We caught him!!!\nUnknown exception in main loop.")

finally:
    # cleanup
    driver.quit()
    if device_type == "RPI":
        display.stop()

    # shutdown
    logger.info("Shutting down.")
    bot_sendtext("debug", logger, "Shutting down.")
    logger.info("This is my last logger action.")
    logger.handlers.clear()
    print("This is my last print action.")
    sys.exit()
