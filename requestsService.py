# -*- coding: utf-8 -*-

### python builtins
from datetime import datetime  # for timestamps
import sys  # for errors

### external libraries
import requests  # for internet traffic

### our own libraries
from loggerService import create_logger
import databaseService as dbs
import telegramService as tgs


# REQUESTS PARAMETERS
my_timeout = 3
my_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0', 'Accept': 'text/html'}
my_verify = True


# prevent sending repeated errors via telegram (on a per-url basis)
error_states = {}
notify_threshold_strict = 1
notify_threshold_permissive = 3

# logging
logger = create_logger("req")


def get_url(url, ws_name=None):
    global error_states
    if not url in error_states:
        error_states[url] = 0
    response = None
    try:
        logger.debug("Getting " + str(url))
        response = requests.get(url, timeout=my_timeout, headers=my_headers, verify=my_verify)
        response.raise_for_status()
        error_states[url] = 0
    except requests.exceptions.HTTPError as e:
        logger.error("An HTTPError has occured while getting " + str(url))
        logger.error("The error is: " + str(e))
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict:
            tgs.send_admin_broadcast("An HTTPError has occured while getting " + str(url))
        if ws_name:
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_msg", argument=str(e))
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_time", argument=datetime.now())
        pass
    except requests.exceptions.ConnectionError as e:
        logger.error("A ConnectionError has occured while getting " + str(url))
        logger.error("The error is: " + str(e))
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict:
            tgs.send_admin_broadcast("A ConnectionError has occured while getting " + str(url))
        if ws_name:
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_msg", argument=str(e))
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_time", argument=datetime.now())
        pass
    except requests.exceptions.Timeout as e:
        logger.error("A timeout has occured while getting " + str(url))
        logger.error("The error is: " + str(e))
        error_states[url] += 1
        if error_states[url] == notify_threshold_permissive:
            tgs.send_admin_broadcast("A timeout has occured while getting " + str(url))
        if ws_name:
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_msg", argument=str(e))
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_time", argument=datetime.now())
        pass
    except requests.exceptions.RequestException as e:
        logger.error("An unknown RequestException has occured while getting " + str(url))
        logger.error("The error is: " + str(e))
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict:
            tgs.send_admin_broadcast("An unknown RequestException has occured while getting " + str(url))
        if ws_name:
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_msg", argument=str(e))
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_time", argument=datetime.now())
        pass
    except Exception:
        logger.error("An unknown exception has occured while getting " + str(url))
        error_msg = str("Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
        logger.error("The error is:" + error_msg)
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict:
            tgs.send_admin_broadcast("An unknown exception has occured while getting " + str(url))
        if ws_name:
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_msg", argument=error_msg)
            dbs.db_websites_set_data(ws_name=ws_name, field="last_error_time", argument=datetime.now())
        pass
    return response
