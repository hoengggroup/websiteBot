import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

import urllib.request
import time
import logging
import sys
from random import randint

from pyvirtualdisplay import Display  # ONLY FOR RPI

from sendTelegram import bot_sendtext


debug = False  # DISABLE WHEN NOT DEBUGGING!!!
loop = True
version = 1.4


# ONLY FOR RPI
display = Display(visible=0, size=(1024, 768))
display.start()

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


URL_TO_SCAN = "http://reservation.livingscience.ch/wohnen"
URL_TO_SCAN_LOCAL = "file:///C:/Users/bingo/polybox/Shared/HWW/livingscience haupt.html"


logger.info("Starting up. Version is " + version)
bot_sendtext("debug", "Starting up. Version is " + version)

firefoxProfile = FirefoxProfile()
# set private mode (as standard)
firefoxProfile.set_preference("browser.privatebrowsing.autostart", True)

driverFire = webdriver.Firefox(firefox_profile=firefoxProfile)

last_alive_signal_time = int(time.time())  # last time when alive signal sent


last_alive_signal_thresh = 1800  # SET THIS FOR DEPLOYMENT!!!
minSleepTime = 45  # SET THIS FOR DEPLOYMENT!!!
maxSleepTime = 90  # SET THIS FOR DEPLOYMENT!!!


# for debugging
whileLoopCounter = 0
whileLoopCounterMax = 1


# check ip
startup_ip = "0.0.0.0"
try:
    with urllib.request.urlopen("https://ipinfo.io/ip") as url:
        startup_ip = (url.read()).decode('utf-8')
        logger.info("Startup IP address is: " + startup_ip)
        bot_sendtext("debug", "Startup IP address is: " + startup_ip)
except Exception as e:
    logger.error("An unknown exception has occured in the initial IP checker subroutine. Error: " + e)
    bot_sendtext("debug", "An unknown exception has occured in the initial IP checker subroutine. Error: " + e)
    loop = False


while loop:
    logger.info("Waking up from sleep and starting next while-loop.")
    # ONLY DEBUG!!!
    if debug:
        whileLoopCounter += 1
        if whileLoopCounter == whileLoopCounterMax:
            URL_TO_SCAN = URL_TO_SCAN_LOCAL


    # check IP address
    try:
        with urllib.request.urlopen("https://ipinfo.io/ip") as url:
            current_ip = (url.read()).decode('utf-8')
            if current_ip != startup_ip:
                logger.error("IP address has changed. New address is " + current_ip + ", while startup IP was " + startup_ip)
                bot_sendtext("debug", "IP address has changed. New address is " + current_ip + ", while startup IP was " + startup_ip)
                break
    except Exception as e:
        logger.error("An unknown exception has occured in the IP checker subroutine. Error: " + e)
        bot_sendtext("debug", "An unknown exception has occured in the IP checker subroutine. Error: " + e)
        break


    # open website
    driverFire.get(URL_TO_SCAN)

    mode = -1


    # check for nodata field
    try:
        nodata_field = driverFire.find_element(By.CLASS_NAME, "nodata")
        logger.debug("nodata text field: found. Text: " + nodata_field.text)
        mode = 0
    except selenium.common.exceptions.NoSuchElementException:
        logger.info("nodata text field: NOT found.")
        mode = 1
    except Exception as e:
        logger.error("An unknown exception has occured in the nodata-field-search subroutine. Error: " + e)
        bot_sendtext("debug", "An unknown exception has occured in the nodata-field-search subroutine. Error: : " + e)
        break


    # check for whgnr field
    try:
        rowWhgnr_field = driverFire.find_element_by_xpath('/html/body/div/div[4]/div[2]/div[2]/div[1]/div/div[2]/div/div/div/div/div[3]/div[2]/span[2]')
        logger.info("whgnr text field: found. Text: " + rowWhgnr_field.text)

        if mode != 1:  # i.e. mode is 0 i.e. nodata field was found
            logger.error("Modes do not match. Mode is " + str(mode) + " but expected mode 1.")
            bot_sendtext("debug", "Modes do not match. Mode is " + str(mode) + " but expected mode 1.")
            break

        logger.info("Free room: " + rowWhgnr_field.text)
        bot_sendtext("shoutout", "Free room: " + rowWhgnr_field.text + "\n" + URL_TO_SCAN)
    except selenium.common.exceptions.NoSuchElementException:
        logger.debug("whgnr text field: NOT found.")

        if (mode != 0):  # i.e. mode is 1 i.e. nodata field was NOT found
            logger.error("Modes do not match. Mode is " + str(mode) + " but expected mode 0.")
            bot_sendtext("debug", "Modes do not match. Mode is " + str(mode) + " but expected mode 0.")
            break
    except Exception as e:
        logger.error("An unknown exception has occured in the whgnr-field-search subroutine. Error: : " + e)
        bot_sendtext("debug", "An unknown exception has occured in the whgnr-field-search subroutine. Error: : " + e)
        break


    # get http response code
    with urllib.request.urlopen(URL_TO_SCAN) as url:
        httpResponseCode = url.getcode()
        if httpResponseCode == 200:
            logger.debug("URL response code: " + str(httpResponseCode) + ", OK.")
        else:
            logger.error("Retrieve error. URL response code is " + str(httpResponseCode) + " but expected 200.")
            bot_sendtext("debug", "Retrieve error. URL response code is " + str(httpResponseCode) + " but expected 200.")
            break


    # alive signal maintainer
    if int(time.time()) - last_alive_signal_time > last_alive_signal_thresh:
        logger.debug("Still alive.")
        bot_sendtext("debug", "Still alive.")
        last_alive_signal_time = int(time.time())

    sleepTime = randint(minSleepTime, maxSleepTime)

    logger.debug("Sleeping for " + str(sleepTime) + " seconds.")

    time.sleep(sleepTime)


driverFire.quit()
display.stop()

logger.info("Shutting down.")
bot_sendtext("debug", "Shutting down.")
