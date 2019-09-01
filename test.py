from main_driver import process_webpage
from main_driver import Webpage
from selenium import webdriver
from pathlib import Path
import platform

import loggerConfig

import multiprocessing # for timeout


multiprocessing.set_start_method('spawn', True)


parent_directory_binaries = str(Path(__file__).resolve().parents[0])
driver = webdriver.Firefox(executable_path=parent_directory_binaries + "/drivers/geckodriver_" + str(platform.system()))
    
webpages_dict = dict()
myWebpage = Webpage("file:///Users/black/Downloads/livingscience%20form.htm",15)
webpages_dict["local"] = myWebpage
current_wbpg_name = "local"

driver_text = driver.find_element_by_tag_name("body").text

logger = loggerConfig.create_logger_main_driver()
if __name__ == '__main__':
    p = multiprocessing.Process(target =process_webpage, args =(logger,driver_text,webpages_dict,current_wbpg_name))
    p.start()
    p.join(10)
