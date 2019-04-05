# -*- coding: utf-8 -*-

import logging


def create_logger():
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

    return logger
