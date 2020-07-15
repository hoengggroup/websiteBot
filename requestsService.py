# -*- coding: utf-8 -*-

### python builtins
from datetime import datetime  # for timestamps
import sys  # for errors

### external libraries
import requests  # for internet traffic

### our own libraries
from configService import my_timeout, my_headers, my_verify, notify_threshold_strict, notify_threshold_permissive
from loggerService import create_logger
import databaseService as dbs
import telegramService as tgs


# logging
logger = create_logger("req")


error_states = {}


def update_database_with_error(ws_name, error):
    error_msg_success = dbs.db_websites_set_data(ws_name=ws_name, field="last_error_msg", argument=str(error))
    error_time_success = dbs.db_websites_set_data(ws_name=ws_name, field="last_error_time", argument=datetime.now())
    if not all([error_msg_success, error_time_success]):
        logger.warning("One or more database updates failed for website " + str(ws_name) + ". It was probably deleted from the database in the meantime.")


def get_url(url, ws_name=None, timeout=my_timeout):
    global error_states
    if not url in error_states:
        error_states[url] = 0
    response = None
    try:
        logger.debug("Getting " + str(url))
        response = requests.get(url, timeout=timeout, headers=my_headers, verify=my_verify)
        response.raise_for_status()
        error_states[url] = 0
    except requests.exceptions.HTTPError as e:
        logger.error("An HTTPError has occured while getting " + str(url))
        logger.error("The error is: " + str(e))
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict:
            tgs.send_admin_broadcast("An HTTPError has occured while getting " + str(url))
        if ws_name:
            update_database_with_error(ws_name, e)
        pass
    except requests.exceptions.ConnectionError as e:
        logger.error("A ConnectionError has occured while getting " + str(url))
        logger.error("The error is: " + str(e))
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict:
            tgs.send_admin_broadcast("A ConnectionError has occured while getting " + str(url))
        if ws_name:
            update_database_with_error(ws_name, e)
        pass
    except requests.exceptions.Timeout as e:
        logger.error("A timeout has occured while getting " + str(url))
        logger.error("The error is: " + str(e))
        error_states[url] += 1
        if error_states[url] == notify_threshold_permissive:
            tgs.send_admin_broadcast("A timeout has occured while getting " + str(url))
        if ws_name:
            update_database_with_error(ws_name, e)
        pass
    except requests.exceptions.RequestException as e:
        logger.error("An unknown RequestException has occured while getting " + str(url))
        logger.error("The error is: " + str(e))
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict:
            tgs.send_admin_broadcast("An unknown RequestException has occured while getting " + str(url))
        if ws_name:
            update_database_with_error(ws_name, e)
        pass
    except Exception:
        logger.error("An unknown exception has occured while getting " + str(url))
        error_msg = str("Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
        logger.error("The error is:" + error_msg)
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict:
            tgs.send_admin_broadcast("An unknown exception has occured while getting " + str(url))
        if ws_name:
            update_database_with_error(ws_name, error_msg)
        pass
    return response
