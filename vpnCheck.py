# -*- coding: utf-8 -*-

import sys
import requests
from requests import get

# our libraries
import telegramService
from loggerConfig import create_logger


def get_ip():
    ip_address = ""
    try:
        response = get('https://api.nordvpn.com/vpn/check/full', timeout=15).json()
        ip_address = response['ip']
        logger.info("IP address is: " + ip_address)

    except requests.exceptions.RequestException as e:
        logger.error("RequestException has occured in the IP/VPN checker module.")
        logger.error("The error is: " + str(e))
        telegramService.send_admin_broadcast("[IP check] Problem: RequestException has occured.")

    except:
        logger.error("An UNKNOWN exception has occured in the ip check subroutine.")
        logger.error("The error is: Arg 0: " + str(sys.exc_info()[0]) + " Arg 1: " + str(sys.exc_info()[1]) + " Arg 2: " + str(sys.exc_info()[2]))
        telegramService.send_admin_broadcast("[IP check] Problem: unknown error")

    return ip_address  # returns empty string on exception


def init():
    global logger
    logger = create_logger("vpn")

    return get_ip()
