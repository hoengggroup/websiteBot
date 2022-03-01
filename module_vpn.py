# -*- coding: utf-8 -*-

# OUR OWN LIBRARIES
from module_logging import create_logger
import module_requests as rqs


# logging
logger = create_logger("vpn")


# variable initialization
ip_address_nordvpn, status_nordvpn, ip_address_icanhazip = [None]*3


def get_nordvpn_api():
    ip_address_nordvpn_tmp = None
    status_nordvpn_tmp = None
    response_nordvpn = rqs.get_url(url="https://nordvpn.com/wp-admin/admin-ajax.php?action=get_user_info_data", timeout=10)
    if response_nordvpn:
        response_nordvpn_json = response_nordvpn.json()
        ip_address_nordvpn_tmp = response_nordvpn_json["ip"]
        status_nordvpn_tmp = response_nordvpn_json["status"]
        logger.debug("The IP address according to NordVPN is {} and the status is {}.".format(ip_address_nordvpn_tmp, status_nordvpn_tmp))
    return ip_address_nordvpn_tmp, status_nordvpn_tmp  # returns None if request fails


def get_icanhazip_api():
    ip_address_icanhazip_tmp = None
    response_icanhazip = rqs.get_url(url="https://ipv4.icanhazip.com/", timeout=10)
    if response_icanhazip:
        ip_address_icanhazip_tmp = response_icanhazip.text.strip()
        logger.debug("The IP address according to Icanhazip is {}.".format(ip_address_icanhazip_tmp))
    return ip_address_icanhazip_tmp  # returns None if request fails


def is_vpn_active():
    ip_address_nordvpn_tmp, status_nordvpn_tmp = get_nordvpn_api()
    ip_address_icanhazip_tmp = get_icanhazip_api()
    if (ip_address_icanhazip == ip_address_icanhazip_tmp) and (ip_address_nordvpn == ip_address_nordvpn_tmp):
        if status_nordvpn_tmp == status_nordvpn:
            logger.debug("VPN is active.")
        else:
            logger.info("The IP address has not changed (which indicates an active VPN connection), but the status reported by NordVPN has.")
        return True
    else:
        logger.warning("VPN is not active.")
        return False


def init(mode="init"):
    if mode == "init":
        global ip_address_nordvpn, status_nordvpn, ip_address_icanhazip

    # check both APIs twice to be extra sure
    # ...also because the "status" (true or false) field in the NordVPN API may still not be 100% reliable
    # ...that is why only one of the status_nordvpn variables need to equal True to validate the VPN connection
    ip_address_nordvpn_1, status_nordvpn_1 = get_nordvpn_api()
    ip_address_icanhazip_1 = get_icanhazip_api()
    ip_address_nordvpn_2, status_nordvpn_2 = get_nordvpn_api()
    ip_address_icanhazip_2 = get_icanhazip_api()

    if ((ip_address_icanhazip_1 == ip_address_icanhazip_2) and (ip_address_nordvpn_1 == ip_address_nordvpn_2) and (ip_address_icanhazip_1 == ip_address_nordvpn_1)
            and ((status_nordvpn_1 is True) or (status_nordvpn_2 is True))):
        ip_address_nordvpn = ip_address_nordvpn_1
        status_nordvpn = True
        ip_address_icanhazip = ip_address_icanhazip_1
        if mode == "re-establish":
            logger.info("Successfully validated re-established connection with VPN.")
        else:
            logger.info("Successfully validated connection with VPN.")
        return True
    else:
        if mode == "re-establish":
            logger.info("Connection with VPN has (still) not been re-established.")
        else:
            logger.error("Could not validate connection with VPN.")
        return False
