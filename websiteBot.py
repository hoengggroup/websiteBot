#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

import urllib.request
import requests # for http requests like IP check. Request to living science page is made with SELENIUM, NOT requests
from requests import get
import time # for sleeping
import logging # for logging
import sys # for getting error info, for exit()
from random import randint # for sleeping random time
from pathlib import Path # for getting super super folder name
import os.path # for getting super super folder name

from sendTelegram import bot_sendtext


# CHECK THESE VARIABLES BEFORE DEPLOYMENT!
# metadata
device = "RPI" #RPI
version = "2.4.2"
# initializations
loop = True
blacklist = {"xxx", "17.506.2"}
# website
websiteURL = "http://reservation.livingscience.ch/wohnen"
# timing
aliveSignalThreshold = 1800
minSleepTime = 45
maxSleepTime = 90
sleepTimeOnNetworkError = 120
sleepCounterDueToNetworkError = 0  # Times slept since last still alive signal. Abbreviation: #slErrCo:
# debugging
debug = False
debugLoopCounter = 0
debugLoopCounterMax = 1
localDebugURL = ""
# modes
MODE_NORMAL = 0
MODE_WAIT_ON_NET_ERROR = 1
mode = MODE_NORMAL
# device_mode
device_mode = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if(device_mode=="LuckyLuke"): # faster on Lucky Luke
    minSleepTime = 10
    maxSleepTime = 30


# log setup
# create logger
logger = logging.getLogger('server_log')
logger.setLevel(logging.DEBUG)
# create file handler and set it to DEBUG level
fh = logging.FileHandler('server_debug.log')
fh.setLevel(logging.DEBUG)
# create file handler and set it to INFO level
fh2 = logging.FileHandler('server_info.log')
fh2.setLevel(logging.INFO)
# create console handler and set it to DEBUG level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
fh2.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(fh2)
logger.addHandler(ch)


# get directory of project
parentDirectory = str(Path(__file__).resolve().parents[0])


# specify imports and selenium drivers for various devices
if device == "RPI":
    from pyvirtualdisplay import Display
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

    display = Display(visible=0, size=(1024, 768))
    display.start()

    firefoxProfile = FirefoxProfile()
    firefoxProfile.set_preference("browser.privatebrowsing.autostart", True)
    driver = webdriver.Firefox(firefox_profile=firefoxProfile)
    driver.set_page_load_timeout(30)

    import sendPushbullet
    sendPushbullet.sendPush("Start", "System just started")
elif device == "manual_firefox_mac" or device == "manual_firefox_win":
    from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

    firefoxProfile = FirefoxProfile()
    firefoxProfile.set_preference("browser.privatebrowsing.autostart", True)
    if device == "manual_firefox_mac":
        driver = webdriver.Firefox(executable_path=parentDirectory+'/drivers/geckodriver_mac', firefox_profile=firefoxProfile)
    elif device == "manual_firefox_win":
        driver = webdriver.Firefox(executable_path=parentDirectory+'/drivers/geckodriver_win.exe', firefox_profile=firefoxProfile)
elif device == "manual_chrome_mac":
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(executable_path=parentDirectory+'/drivers/chromedriver_mac', options=chrome_options)
else:
    logger.error("Invalid device type. Exiting.")
    sys.exit()


# startup
logger.info("Starting up. Current version is: " + version + " Device is: " + device)
bot_sendtext("debug", logger, "Starting up.\nCurrent version is: " + version + "\nDevice is: " + device)
lastAliveSignalTime = int(time.time())


# initial IP address check
startup_ip = "0.0.0.0"
try:
    startup_ip = get('https://api.ipify.org').text
    logger.info("Startup IP address is: " + startup_ip)
    bot_sendtext("debug", logger, "Startup IP address is: " + startup_ip)
except requests.exceptions.RequestException as e:
    logger.error("RequestException has occured in the initial IP checker subroutine.")
    logger.error("The error is: " + str(e))
    bot_sendtext("debug", logger, "RequestException has occured in the initial IP checker subroutine.")
    loop = False

# main loop
try:
    while loop:
        if mode==MODE_NORMAL:
            logger.debug("Waking up from sleep. Normal mode")
            # test with local saved webpage when debugging
            if debug:
                debugLoopCounter += 1
                if debugLoopCounter == debugLoopCounterMax:
                    websiteURL = localDebugURL

            # subsequent IP address check
            try:
                current_ip = get('https://api.ipify.org').text
                if "a" in current_ip or "e" in current_ip or "h" in current_ip:  # is this right contains?
                    logger.error("IP request contains letters. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                    bot_sendtext("debug", logger, "IP request contains letters. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                    mode = MODE_WAIT_ON_NET_ERROR
                    continue
                if current_ip != startup_ip:
                    logger.error("IP address has changed. New address is " + current_ip + ", while startup IP was " + startup_ip)
                    bot_sendtext("debug", logger, "IP address has changed.\nNew address is " + current_ip + ", while startup IP was " + startup_ip)
                    bot_sendtext("debug", logger, "Please restart VPN service as soon as possible. Entering hibernation.")
                    # keep script running senselessly
                    while True:
                        time.sleep(3600)
            except requests.exceptions.RequestException as e:
                logger.error("RequestException has occured in the IP checker subroutine. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                bot_sendtext("debug", logger, "RequestException has occured in the IP checker subroutine. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                mode = MODE_WAIT_ON_NET_ERROR
                continue

            try:
                # open website
                logger.debug("Getting website")
                driver.get(websiteURL)
                logger.debug("Got website")

                # check website content
                # maybe wrap in try-catch
                rowWhgnr_field = list(driver.find_elements_by_class_name("spalte7"))
                logger.debug("Got rowWhgnr")
                logger.debug("Length: "+str(len(rowWhgnr_field)))
                rowWhgnr_field = rowWhgnr_field[1:]  # delete title of column
                logger.debug("Cut rowWhgnr field")
            except selenium.common.exceptions.TimeoutException as e:
                logger.error("TimeoutException has occured in the row whgnr retreival subroutine. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                bot_sendtext("debug", logger, "TimeoutException has occured in the row whgnr retreival subroutine. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                mode = MODE_WAIT_ON_NET_ERROR
                continue
            except selenium.common.exceptions.WebDriverException as e:
                logger.error("WebDriverException has occured in the row whgnr retreival subroutine. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                bot_sendtext("debug", logger, "WebDriverException has occured in the row whgnr retreival subroutine. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                mode = MODE_WAIT_ON_NET_ERROR
                continue
            except:
                logger.error("An UNKNOWN exception has occured in the main loop.")
                logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
                mode = MODE_WAIT_ON_NET_ERROR
                continue


            if len(rowWhgnr_field) == 0:
                logger.debug("No whgnrs found.")
            else:
                if device == "RPI":
                    sendPushbullet.processbullet(rowWhgnr_field)
                debugString = ""
                shoutoutString = ""
                for room in rowWhgnr_field:
                    logger.info("whgnr text field found. Text: " + room.text)
                    if room.text not in blacklist:
                        shoutoutString += room.text + "\n"
                    else:
                        debugString += room.text + "\n"
                if shoutoutString:
                    bot_sendtext("shoutout", logger, shoutoutString + websiteURL)
                bot_sendtext("debug", logger, debugString + "---------")

            # get http response code
            try:
                logger.debug("Getting http response")
                httpResponseCode = get(websiteURL).status_code
                logger.debug("Got http response")
                if httpResponseCode == 200:
                    logger.debug("URL response code: " + str(httpResponseCode) + ", OK.")
                else:
                    logger.error("Retrieve error. URL response code is " + str(httpResponseCode) + " but expected 200.")
                    bot_sendtext("debug", logger, "Retrieve error. URL response code is " + str(httpResponseCode) + " but expected 200.")
            except requests.exceptions.RequestException as e:
                logger.error("RequestException has occured in the HTTP response code checker subroutine. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                logger.error("The error is: " + str(e))
                bot_sendtext("debug", logger, "RequestException has occured in the HTTP response code checker subroutine. Sleeping now for " + str(sleepTimeOnNetworkError) + "s; retrying then.")
                mode = MODE_WAIT_ON_NET_ERROR
                continue

            # alive signal maintainer
            if int(time.time()) - lastAliveSignalTime > aliveSignalThreshold:
                logger.debug("Still alive #slErrCo: "+str(sleepCounterDueToNetworkError))
                bot_sendtext("debug", logger, "Still alive. #slErrCo: " + str(sleepCounterDueToNetworkError))
                lastAliveSignalTime = int(time.time())
                sleepCounterDueToNetworkError = 0

            # sleeping
            sleepTime = randint(minSleepTime, maxSleepTime)
            logger.debug("Sleeping for " + str(sleepTime) + " seconds.")
            time.sleep(sleepTime)
        elif mode == MODE_WAIT_ON_NET_ERROR:
            logger.info("Sleeping now in NET ERROR mode")
            time.sleep(sleepTimeOnNetworkError)
            sleepCounterDueToNetworkError += 1
            logger.info("Woke up from NET ERROR mode sleep")
            mode = MODE_NORMAL
        else:
            logger.error("UNKNOWN MODE")
            bot_sendtext("debug",logger,"Error: Unknown mode.")
except:
    logger.error("An UNKNOWN exception has occured in the main loop.")
    logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
    bot_sendtext("debug", logger, "We caught him!!!\nUnknown exception in main loop.")
finally:
    # cleanup
    driver.quit()
    if device == "RPI":
        display.stop()

    # shutdown
    logger.info("Shutting down.")
    bot_sendtext("debug", logger, "Shutting down.")
    logger.info("This is my last logger action.")
    logger.handlers.clear()
    print("This is my last print action.")
    sys.exit()
