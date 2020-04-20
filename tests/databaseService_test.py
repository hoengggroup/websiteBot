#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from datetime import datetime

import databaseService as dbs

connection_state = dbs.db_connect()
if not connection_state:
    sys.exit()

print(connection_state)
print("--------")


#print("Creating users")
#dbs.db_users_create(12345678, 2, "aaa", "bbbb", "user_1", "user_1_app", "hi id like to join", "2019-06-16")
#dbs.db_users_create(14653466, 2, "ccccc", "ffffffff", "user_2", "user_2_app", "hi id like to join", "2019-09-04")
#dbs.db_users_create(34545346, 2, "gg", "hhh", "user_3", "user_3_app", "hi id like to join", "2019-12-31")
#dbs.db_users_create(74564533, 2, "asdfghjklö", "qwertzuiop", "user_4", "user_4_app", "hi id like to join", "2020-01-12")
#dbs.db_users_create(98754342, 2, "yxcvbnm", "jkrwjksbkjwebk", "user_5", "user_5_app", "hi id like to join", "2020-02-28")
#dbs.db_users_create(99674542, 2, "foobar", "helloworld", "user_6", "user_6_app", "hi id like to join", "2020-03-12")
#dbs.db_users_create(99999999, 2, "aadcdca", "csdvsv", "user_7", "user_7_app", "hi id like to join", "2020-04-12")
#print("--------")


#print("Deleting users")
#dbs.db_users_delete(74564533)
#dbs.db_users_delete(99999999)
#print("--------")


#print("Checking if user exists")
#exists_1 = dbs.db_users_exists(74564533)
#exists_2 = dbs.db_users_exists(34545346)
#print(exists_1)
#print(exists_2)
#print("--------")


#print("Getting user id list")
#ids = dbs.db_users_get_all_ids()
#print(ids)
#print("--------")


#print("Getting user data")
#user_data_1 = dbs.db_users_get_data(77777777, "foo")
#user_data_2 = dbs.db_users_get_data(34545346, "status")
#print(user_data_1)
#print(user_data_2)
#print("--------")


#print("Setting user data")
#dbs.db_users_set_data(99674542, "apply_text", "lorem ipsum dolor sit amet")
#print("--------")


#print("Getting all user data")
#ids = dbs.db_users_get_ids()
#for i in ids:
    #user_data = dbs.db_users_get_data(i, "all_fields")
    #print(user_data)
#print("--------")


#print("Getting website id from name")
#ws_id_1 = dbs.db_websites_get_id("google")
#ws_id_2 = dbs.db_websites_get_id("ard")
#print(ws_id_1)
#print(ws_id_2)
#print("--------")


#print("Getting website name from id")
#name_1 = dbs.db_websites_get_name(21)
#name_2 = dbs.db_websites_get_name(70)
#print(name_1)
#print(name_2)
#print("--------")


#print("Getting website id list")
#ids = dbs.db_websites_get_all_ids()
#print(ids)
#print("--------")


#print("Adding websites")
#dbs.db_websites_add("orf", "news.orf.at", 10, datetime.min, datetime.now(), None, None, None)
#dbs.db_websites_add("google", "google.at", 10, datetime.min, datetime.now(), None, None, None)
#dbs.db_websites_add("srf", "srf.ch", 10, datetime.min, datetime.now(), None, None, None)
#print("--------")


#print("Removing websites")
#dbs.db_websites_remove("ard")
#dbs.db_websites_remove("google")
#print("--------")


#print("Getting website data")
#ws_data_1 = dbs.db_websites_get_data("srf", "foo")
#ws_data_2 = dbs.db_websites_get_data("orf", "url")
#ws_data_3 = dbs.db_websites_get_data("ard", "foo")
#print(ws_data_1)
#print(ws_data_2)
#print(ws_data_3)
#print("--------")


#print("Setting website data")
#dbs.db_websites_set_data("srf", "url", "srf.ch")
#dbs.db_websites_set_data("orf", "last_time_updated", datetime.now())
#dbs.db_websites_set_data("google", "last_content", "lorem ipsum dolor sit amet")
#dbs.db_websites_set_data("ard", "last_hash", "aaaaaaaaaaaaaaaaa")
#print("--------")


#print("Getting all website data")
#ids = dbs.db_websites_get_all_ids()
#for i in ids:
    #name = dbs.db_websites_get_name(i)
    #website_data = dbs.db_websites_get_data(*name)
    #print(website_data)
#print("--------")


#print("Getting subscriptions by website")
#subs_1 = dbs.db_subscriptions_by_website("orf")
#print(subs_1)
#subs_2 = dbs.db_subscriptions_by_website("google")
#print(subs_2)
#subs_3 = dbs.db_subscriptions_by_website("ard")
#print(subs_3)
#print("--------")


#print("Getting subscriptions by user")
#subs_1 = dbs.db_subscriptions_by_user(14653466)
#print(subs_1)
#subs_2 = dbs.db_subscriptions_by_user(77777777)
#print(subs_2)
#subs_3 = dbs.db_subscriptions_by_user(34545346)
#print(subs_3)
#print("--------")


#print("Checking specific subscription")
#subbed_1 = dbs.db_subscriptions_check(14653466, 21)
#print(subbed_1)
#subbed_2 = dbs.db_subscriptions_check(14653466, 34)
#print(subbed_2)
#subbed_3 = dbs.db_subscriptions_check(14653466, dbs.db_websites_get_id("google"))
#print(subbed_3)
#subbed_4 = dbs.db_subscriptions_check(77777777, dbs.db_websites_get_id("srf"))
#print(subbed_4)
#subbed_5 = dbs.db_subscriptions_check(12345678, dbs.db_websites_get_id("ard"))
#print(subbed_5)
#print("--------")


#print("Subscribing")
#dbs.db_subscriptions_subscribe(14653466, "srf")
#dbs.db_subscriptions_subscribe(14653466, "orf")
#dbs.db_subscriptions_subscribe(14653466, "google")
#dbs.db_subscriptions_subscribe(34545346, "orf")
#dbs.db_subscriptions_subscribe(12345678, "google")
#print("--------")


#print("Unsubscribing")
#dbs.db_subscriptions_unsubscribe(74564533, "srf")
#dbs.db_subscriptions_unsubscribe(74564533, "orf")
#dbs.db_subscriptions_unsubscribe(74564533, "google")
#dbs.db_subscriptions_unsubscribe(34545346, "orf")
#dbs.db_subscriptions_unsubscribe(12345678, "google")
#dbs.db_subscriptions_unsubscribe(12345678, "srf")
#dbs.db_subscriptions_unsubscribe(77777777, "srf")
#dbs.db_subscriptions_unsubscribe(12345678, "ard")
#print("--------")


status = dbs.db_disconnect()
print(status)
