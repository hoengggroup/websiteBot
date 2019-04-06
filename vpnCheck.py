# -*- coding: utf-8 -*-

import requests
from requests import get
import time

from sendTelegram import bot_sendtext
from globalConfig import mode_wait_on_net_error
from websiteConfig_1 import get_timeout, sleep_time_on_network_error


def vpn_check(logger, notify, ip_address, mode):
    try:
        response = get('https://api.nordvpn.com/vpn/check/full', timeout=get_timeout).json()
        logger.info("IP address is: " + response['ip'])
        logger.info("VPN status is (unreliable): " + response['status'])
        if notify or response['status'] != "Protected":
            bot_sendtext("debug", logger, "IP address is: " + response['ip'] + "\nVPN status is (unreliable): " + response['status'])
            if response['ip'] == ip_address and ip_address != "0.0.0.0":
                logger.info("IP address has not changed (reliable).")
                bot_sendtext("debug", logger, "IP address has not changed (reliable).")

        if response['ip'] != ip_address and ip_address != "0.0.0.0":
            logger.info("IP address has changed. Please restart VPN service as soon as possible. Entering hibernation.")
            bot_sendtext("debug", logger, "IP address has changed. Please restart VPN service as soon as possible. Entering hibernation.")
            # keep script running senselessly
            while True:
                time.sleep(3600)

        ip_address = response['ip']

    except requests.exceptions.RequestException as e:
        logger.error("RequestException has occured in the IP/VPN checker module.")
        logger.error("The error is: " + str(e))
        bot_sendtext("debug", logger, "RequestException has occured in the IP/VPN checker module. Sleeping now for " + str(sleep_time_on_network_error) + "s; retrying then.")
        mode = mode_wait_on_net_error

    return ip_address, mode
