# -*- coding: utf-8 -*-

import requests
from requests import get
import time

# our libraries
import telegramService
from loggerConfig import create_logger_vpn


def get_ip():
    try:
        response = get('https://api.nordvpn.com/vpn/check/full', timeout=15).json()
        ip_address = response['ip']
        logger.info("IP address is: " + ip_address)

    except requests.exceptions.RequestException as e:
        logger.error("RequestException has occured in the IP/VPN checker module.")
        logger.error("The error is: " + str(e))
        telegramService.send_admin_broadcast("RequestException has occured in the IP/VPN checker module.")

    return ip_address


def init():
    global logger
    logger = create_logger_vpn()

    return get_ip()
