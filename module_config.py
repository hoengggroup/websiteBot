# -*- coding: utf-8 -*-

# PYTHON BUILTINS
from pathlib import Path


# MAIN PARAMETERS
version_code = "6.2"
keep_website_history = False


# DATABASE PARAMETERS
# url schema: postgresql://user:password@netloc:port/dbname
pg_string = Path('./secrets/pg_string.txt').read_text()


# REQUESTS PARAMETERS
my_timeout = 3
my_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0', 'Accept': 'text/html'}
my_verify = True
notify_threshold_strict = 1  # all requests errors except timeouts
notify_threshold_permissive = 5  # only timeouts
