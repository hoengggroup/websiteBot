# -*- coding: utf-8 -*-

### our own libraries
from loggerService import create_logger
import requestsService as rqs


# logging
logger = create_logger("vpn")


def get_nordvpn_api():
    ip_address_nordvpn_tmp = None
    status_nordvpn_tmp = None
    response_nordvpn = rqs.get_url(url="https://api.nordvpn.com/vpn/check/full").json()
    if response_nordvpn:
        ip_address_nordvpn_tmp = response_nordvpn["ip"]
        status_nordvpn_tmp = response_nordvpn["status"]
        logger.debug("The IP address according to NordVPN is " + ip_address_nordvpn_tmp + " and the status is \"" + status_nordvpn_tmp + "\".")
    return ip_address_nordvpn_tmp, status_nordvpn_tmp  # returns None if request fails


def get_ipify_api():
    ip_address_ipify_tmp = None
    response_ipify = rqs.get_url(url="https://api.ipify.org?format=json").json()
    if response_ipify:
        ip_address_ipify_tmp = response_ipify["ip"]
        logger.debug("The IP address according to Ipify is " + ip_address_ipify_tmp + ".")
    return ip_address_ipify_tmp  # returns None if request fails


def is_vpn_active():
    ip_address_nordvpn_tmp, status_nordvpn_tmp = get_nordvpn_api()
    ip_address_ipify_tmp = get_ipify_api()
    if (ip_address_ipify == ip_address_ipify_tmp) and (ip_address_nordvpn == ip_address_nordvpn_tmp):
        if status_nordvpn_tmp == status_nordvpn:
            logger.debug("VPN is active.")
        else:
            logger.info("The IP address has not changed (which indicates an active VPN connection), but the status reported by NordVPN has.")
        return True
    else:
        logger.warning("VPN is not active.")
        return False


def init(mode="init"):
    if mode=="init":
        global ip_address_nordvpn, status_nordvpn, ip_address_ipify

    # check both APIs twice to be extra sure
    # ...also because the "status" (protected or unprotected) field in the NordVPN API is still not 100% reliable
    # ...that is why only one of the status_nordvpn variables need to equal "Protected" to validate the VPN connection
    ip_address_nordvpn_1, status_nordvpn_1 = get_nordvpn_api()
    ip_address_ipify_1 = get_ipify_api()
    ip_address_nordvpn_2, status_nordvpn_2 = get_nordvpn_api()
    ip_address_ipify_2 = get_ipify_api()

    if ((ip_address_ipify_1 == ip_address_ipify_2) and (ip_address_nordvpn_1 == ip_address_nordvpn_2) and (ip_address_ipify_1 == ip_address_nordvpn_1)
        and ((status_nordvpn_1 == "Protected") or (status_nordvpn_2 == "Protected"))):
        ip_address_nordvpn = ip_address_nordvpn_1
        status_nordvpn = "Protected"
        ip_address_ipify = ip_address_ipify_1
        if mode=="re-establish":
            logger.info("Successfully validated re-established connection with VPN.")
        else:
            logger.info("Successfully validated connection with VPN.")
        return True
    else:
        if mode=="re-establish":
            logger.info("Connection with VPN has (still) not been re-established.")
        else:
            logger.error("Could not validate connection with VPN.")
        return False
