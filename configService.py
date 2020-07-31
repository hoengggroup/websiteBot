# -*- coding: utf-8 -*-

# MAIN PARAMETERS
version_code = "5.6.1"
keep_website_history = True
filter_dict = {'living': ['17.509', '17.515', '13.613', '13.615', '13.617', '13.619',
                          '17.511', '17.513', '17.503', '17.505', '17.507', '13.605', '13.607', '13.609', '13.611']}


# DATABASE PARAMETERS
my_database = "websitebot_db"
my_user = "websitebot"
my_password = "webSiteBotPostGresQL"
my_host = "localhost"
my_port = "5432"


# REQUESTS PARAMETERS
my_timeout = 3
my_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0', 'Accept': 'text/html'}
my_verify = True
notify_threshold_strict = 1  # all requests errors except timeouts
notify_threshold_permissive = 3  # only timeouts
