# -*- coding: utf-8 -*-

import sys

from sendTelegram import bot_sendtext
from globalConfig import device_type, mode_wait_on_net_error


website_URL = "http://reservation.livingscience.ch/wohnen"

room_blacklist = {"xxx", "17.506.2"}

# timing
alive_signal_threshold = 1800
min_sleep_time = 5
max_sleep_time = 30
sleep_time_on_network_error = 120
sleep_counter_due_to_network_error = 0   # Times slept in net error mode since last still alive signal. Abbreviation: #slErrCo:
get_timeout = 15  # Timeout in seconds for get requests. If no timeout is set, it waits endlessly.


def check_livingscience(driver, logger, mode):
    try:
        rowWhgnr_field = list(driver.find_elements_by_class_name("spalte7"))
        logger.debug("Got rowWhgnr")
        rowWhgnr_field = rowWhgnr_field[1:]  # delete title of column
        logger.debug("Length (= number of rooms): " + str(len(rowWhgnr_field)))

        if len(rowWhgnr_field) == 0:
            logger.debug("No whgnrs found.")

        else:
            if device_type == "RPI":
                from sendPushbullet import process_bullet
                process_bullet(rowWhgnr_field)

            debugString = ""
            liveString = ""
            for room in rowWhgnr_field:
                logger.info("whgnr text field found. Text: " + room.text)

                if room.text not in room_blacklist:
                    liveString += room.text + "\n"

                else:
                    debugString += room.text + "\n"

            if liveString:
                bot_sendtext("live", logger, liveString + website_URL)

            bot_sendtext("debug", logger, debugString + "---------")

    except:
        logger.error("An UNKNOWN exception has occured in the website checker module.")
        logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
        mode = mode_wait_on_net_error

    return rowWhgnr_field, mode
