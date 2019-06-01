# -*- coding: utf-8 -*-

from selenium import webdriver
from pathlib import Path
import platform



parent_directory_binaries = str(Path(__file__).resolve().parents[0])

driver = webdriver.Firefox(executable_path=parent_directory_binaries + "/drivers/geckodriver_" + str(platform.system()))
driver.set_page_load_timeout(10)

driver.get("https://www.cookie-checker.com/")
website_text = driver.find_element_by_tag_name("body").text

print(website_text)



from selenium import webdriver

driver = webdriver.Firefox())
driver.set_page_load_timeout(10)

driver.get("https://www.cookie-checker.com/")
website_text = driver.find_element_by_tag_name("body").text

print(website_text)