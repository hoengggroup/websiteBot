#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import databaseService as dbs

status = dbs.db_connect()

print(status)
print("--------")

print("Creating a new user")
dbs.db_create_user(1009, "test", "run3", "2020-04-12")
print("--------")

print("Getting user id list")
ids = dbs.db_get_user_ids()
ids = [item for t in ids for item in t]
print(ids)
print("--------")

print("Getting user info for all ids")
for i in ids:
    (user_id, fname, lname, date, group) = dbs.db_get_user_info(i)
    print(user_id, fname, lname, date, group)
print("--------")

status_2 = dbs.db_disconnect()

print(status_2)
