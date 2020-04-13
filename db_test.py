#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import databaseService as dbs

status = dbs.db_connect()

print(status)
print("--------")

# Only test when necessary, let's not pump it full of junk
'''
print("Creating a new user")
dbs.db_create_user(1009, "test", "run3", "2020-04-12")
print("--------")
'''

print("Getting user id list")
ids = dbs.db_get_user_ids()
ids = [item for t in ids for item in t]
print(ids)
print("--------")

# Currently would not work, the arguments are mismatched after the rewrite and it's 2am
'''
print("Getting user info for all ids")
for i in ids:
    (user_id, fname, lname, date, group) = dbs.db_get_user_info(i)
    print(user_id, fname, lname, date, group)
print("--------")
'''

status_2 = dbs.db_disconnect()

print(status_2)
