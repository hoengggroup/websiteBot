# -*- coding: utf-8 -*-

# PYTHON BUILTINS
from datetime import datetime  # for timestamps

# EXTERNAL LIBRARIES
import requests  # for internet traffic

# OUR OWN LIBRARIES
from module_config import my_timeout, my_headers, my_verify, notify_threshold_strict, notify_threshold_permissive
from module_logging import create_logger, exception_printing
import module_database as dbs
import module_telegram as tgs


# logging
logger = create_logger("req")


error_states = {}


def update_database_with_error(ws_name, error):
    error_msg_success = dbs.db_websites_set_data(ws_name=ws_name, field="last_error_msg", argument=error)
    error_time_success = dbs.db_websites_set_data(ws_name=ws_name, field="last_error_time", argument=datetime.now())
    if not all([error_msg_success, error_time_success]):
        logger.warning("One or more database updates failed for website {}. It was probably deleted from the database in the meantime.".format(ws_name))


def get_url(url, ws_name=None, timeout=my_timeout):
    global error_states  # pylint: disable=global-variable-not-assigned
    if url not in error_states:
        error_states[url] = 0
    response = None
    try:
        logger.debug("Getting {}".format(url))
        response = requests.get(url, timeout=timeout, headers=my_headers, verify=my_verify)
        response.raise_for_status()
        error_states[url] = 0
    except requests.exceptions.RequestException as e:
        exctype, exc, tb = exception_printing(e)
        logger.error("A requests.{} has occured in the requests module while getting {}\nError message: {}\nTraceback:\n{}".format(exctype, url, exc, tb))
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict and exctype != "Timeout":
            tgs.send_admin_broadcast("A requests.{} has occured in the requests module while getting {}\nError message: {}\nTraceback:\n{}".format(exctype, url, tgs.convert_less_than_greater_than(exc), tgs.convert_less_than_greater_than(tb)))
        elif error_states[url] == notify_threshold_permissive and exctype == "Timeout":
            tgs.send_admin_broadcast("A requests.{} has occured in the requests module while getting {}\nError message: {}\nTraceback:\n{}".format(exctype, url, tgs.convert_less_than_greater_than(exc), tgs.convert_less_than_greater_than(tb)))
        if ws_name:
            update_database_with_error(ws_name, "{}: {}".format(exctype, exc))
        pass
    except Exception as e:
        exctype, exc, tb = exception_printing(e)
        logger.error("A {} has occured in the requests module while getting {}\nError message: {}\nTraceback:\n{}".format(exctype, url, exc, tb))
        error_states[url] += 1
        if error_states[url] == notify_threshold_strict:
            tgs.send_admin_broadcast("A {} has occured in the requests module while getting {}\nError message: {}\nTraceback:\n{}".format(exctype, url, tgs.convert_less_than_greater_than(exc), tgs.convert_less_than_greater_than(tb)))
        if ws_name:
            update_database_with_error(ws_name, "{}: {}".format(exctype, exc))
        pass
    return response
