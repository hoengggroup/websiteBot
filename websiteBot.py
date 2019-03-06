#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

import urllib.request
from requests import get
import time
import logging
import sys
from random import randint
from pathlib import Path

from sendTelegram import bot_sendtext


# CHECK THESE VARIABLES BEFORE DEPLOYMENT!
# metadata
device = "RPI"
version = "2.1.3"
# initializations
loop = True
parsingMode = -1
# website
websiteURL = "http://reservation.livingscience.ch/wohnen"
# timing
aliveSignalThreshold = 1800
minSleepTime = 45
maxSleepTime = 90
# debugging
debug = False
debugLoopCounter = 0
debugLoopCounterMax = 1
localDebugURL = ""


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
bot_sendtext("debug", "Starting up.\nCurrent version is: " + version + "\nDevice is: " + device)
lastAliveSignalTime = int(time.time())


# initial IP address check
startup_ip = "0.0.0.0"
try:
    startup_ip = get('https://api.ipify.org').text
    logger.info("Startup IP address is: " + startup_ip)
    bot_sendtext("debug", "Startup IP address is: " + startup_ip)
except Exception as e:
    logger.error("An unknown exception has occured in the initial IP checker subroutine. Error: " + e)
    bot_sendtext("debug", "An unknown exception has occured in the initial IP checker subroutine.\nError: " + e)
    loop = False


# main loop
try:
    while loop:
        logger.info("Waking up from sleep and starting next while-loop.")

        # test with local saved webpage when debugging
        if debug:
            debugLoopCounter += 1
            if debugLoopCounter == debugLoopCounterMax:
                websiteURL = localDebugURL

        # subsequent IP address check
        try:
            current_ip = get('https://api.ipify.org').text
            if current_ip != startup_ip:
                logger.error("IP address has changed. New address is " + current_ip + ", while startup IP was " + startup_ip)
                bot_sendtext("debug", "IP address has changed.\nNew address is " + current_ip + ", while startup IP was " + startup_ip)
                break
        except Exception as e:
            logger.error("An unknown exception has occured in the IP checker subroutine. Error: " + e)
            bot_sendtext("debug", "An unknown exception has occured in the IP checker subroutine.\nError: " + e)
            break

        # open website
        driver.get(websiteURL)

        # check for nodata field
        try:
            nodata_field = driver.find_element(By.CLASS_NAME, "nodata")
            logger.debug("nodata text field: found. Text: " + nodata_field.text)
            parsingMode = 0
        except selenium.common.exceptions.NoSuchElementException:
            logger.info("nodata text field: NOT found.")
            parsingMode = 1
        except Exception as e:
            logger.error("An unknown exception has occured in the nodata-field-search subroutine. Error: " + e)
            bot_sendtext("debug", "An unknown exception has occured in the nodata-field-search subroutine.\nError: " + e)
            break

        # check for whgnr field
        try:
            rowWhgnr_field = driver.find_element_by_xpath('/html/body/div/div[4]/div[2]/div[2]/div[1]/div/div[2]/div/div/div/div/div[3]/div[2]/span[2]')
            logger.info("whgnr text field: found. Text: " + rowWhgnr_field.text)
            if parsingMode != 1:  # i.e. parsing mode is 0 i.e. nodata field was found
                logger.error("Modes do not match. Mode is " + str(parsingMode) + " but expected mode 1.")
                bot_sendtext("debug", "Modes do not match. Mode is " + str(parsingMode) + " but expected mode 1.")
                break
            logger.warning("Free room: " + rowWhgnr_field.text)
            bot_sendtext("shoutout", "Free room: " + rowWhgnr_field.text + "\n" + websiteURL)
        except selenium.common.exceptions.NoSuchElementException:
            logger.debug("whgnr text field: NOT found.")
            if parsingMode != 0:  # i.e. parsing mode is 1 i.e. nodata field was NOT found
                logger.error("Modes do not match. Mode is " + str(parsingMode) + " but expected mode 0.")
                bot_sendtext("debug", "Modes do not match. Mode is " + str(parsingMode) + " but expected mode 0.")
                break
        except Exception as e:
            logger.error("An unknown exception has occured in the whgnr-field-search subroutine. Error: " + e)
            bot_sendtext("debug", "An unknown exception has occured in the whgnr-field-search subroutine.\nError: " + e)
            break

        # get http response code
        with urllib.request.urlopen(websiteURL) as url:
            httpResponseCode = url.getcode()
            if httpResponseCode == 200:
                logger.debug("URL response code: " + str(httpResponseCode) + ", OK.")
            else:
                logger.error("Retrieve error. URL response code is " + str(httpResponseCode) + " but expected 200.")
                bot_sendtext("debug", "Retrieve error. URL response code is " + str(httpResponseCode) + " but expected 200.")
                break

        # alive signal maintainer
        if int(time.time()) - lastAliveSignalTime > aliveSignalThreshold:
            logger.debug("Still alive.")
            bot_sendtext("debug", "Still alive.")
            lastAliveSignalTime = int(time.time())

        # sleeping
        sleepTime = randint(minSleepTime, maxSleepTime)
        logger.debug("Sleeping for " + str(sleepTime) + " seconds.")
        time.sleep(sleepTime)
except Exception as e:
    logger.error("An unknown exception has occured in the main loop. Error: " + e)
    bot_sendtext("debug", "We caught him!!!\nUnknown exception in main loop.\nError: " + e)
finally:
    # cleanup
    driver.quit()
    if device == "RPI":
        display.stop()

    # shutdown
    logger.info("Shutting down.")
    bot_sendtext("debug", "Shutting down.")
    logger.handlers.clear()
    sys.exit()
