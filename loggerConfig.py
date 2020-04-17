# -*- coding: utf-8 -*-

import logging
import textwrap  # for aligning the log message into a column


class WrappedFixedIndentingLog(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%', width=192, indent=45):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.wrapper = textwrap.TextWrapper(width=width, subsequent_indent=' '*indent)
    def format(self, record):
        return self.wrapper.fill(super().format(record))


class ModuleFilterMain(logging.Filter):
    def filter(self, record):
        record.module_tag = "[MAIN]:"
        return True


class ModuleFilterDB(logging.Filter):
    def filter(self, record):
        record.module_tag = "[DB]:"
        return True


class ModuleFilterTG(logging.Filter):
    def filter(self, record):
        record.module_tag = "[TG]:"
        return True


class ModuleFilterVPN(logging.Filter):
    def filter(self, record):
        record.module_tag = "[VPN]:"
        return True


def create_logger(module):
    # create logger
    logger = logging.getLogger(str(module)+"_log")
    logger.setLevel(logging.DEBUG)

    # create file handler and set it to DEBUG level
    fh = logging.FileHandler(str(module)+"_debug.log")
    fh.setLevel(logging.DEBUG)
    # create file handler and set it to INFO level
    fh2 = logging.FileHandler(str(module)+"_info.log")
    fh2.setLevel(logging.INFO)
    # create console handler and set it to DEBUG level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # add filter depending on the module
    if module == "main":
        logger.addFilter(ModuleFilterMain())
    elif module == "db":
        logger.addFilter(ModuleFilterDB())
    elif module == "tg":
        logger.addFilter(ModuleFilterTG())
    elif module == "vpn":
        logger.addFilter(ModuleFilterVPN())
    else:
        del logger
        return

    # create (custom) formatter and add it to the handlers
    formatter = WrappedFixedIndentingLog("%(asctime)s - %(levelname)-8s - %(module_tag)-7s %(message)s", width=192, indent=45)
    fh.setFormatter(formatter)
    fh2.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(fh2)
    logger.addHandler(ch)

    return logger
