# -*- coding: utf-8 -*-

# This is a file to test the getting subroutine of the system
# Please upstream any changes to the get method and header to the main_driver.py
# Parameters should always be synced

import requests  # for internet traffic

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/74.0',
    'Accept': 'text/html'
}

current_url = "https://www.ds3lab.com/dmdb-2020/"
website_load_timeout = 10

rContent = requests.get(current_url, timeout=website_load_timeout, headers=headers, verify=False)
print(rContent.status_code)
print(rContent.text[:min(200, len(rContent.text))])  # print only first part
