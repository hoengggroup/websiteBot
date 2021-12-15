# -*- coding: utf-8 -*-

# MAIN PARAMETERS
version_code = "6.0"
keep_website_history = True


# DATABASE PARAMETERS
# url schema: postgresql://user:password@netloc:port/dbname
pg_string = "postgresql://websitebot:webSiteBotPostGresQL@localhost:5432/websitebot_db"


# REQUESTS PARAMETERS
my_timeout = 3
my_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0', 'Accept': 'text/html'}
my_verify = True
notify_threshold_strict = 1  # all requests errors except timeouts
notify_threshold_permissive = 3  # only timeouts
