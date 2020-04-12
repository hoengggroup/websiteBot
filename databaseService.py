#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2 import errorcodes


# DATABASE PARAMETERS
my_database = "postgres"
my_user = "black"
my_password = ""
my_host = "localhost"
my_port = "5432"


# Amazing (self-created ;)) error handler.
# Common errors should be added following the pattern of the UNIQUE_VIOLATION error.
def db_exc_handler(excp, conn):
    print("Error: " + str(excp.pgcode))
    if(excp.pgcode == errorcodes.UNIQUE_VIOLATION):
        print("Key error. Details: " + str(excp))
        conn.rollback()
    else:
        print("Unkown error " + str(excp.pgcode) + " Lookup: " + errorcodes.lookup(excp.pgcode))


# CONNECT TO DATABASE
def db_connect():
    global conn
    global cur
    try:
        conn = psycopg2.connect(database=my_database, user=my_user, password=my_password, host=my_host, port=my_port)
        print("Successfully connected to database.")
    except Exception as ex:
        print("Could not connect to database. Error: '%s'" % str(ex))
        return -1
    try:
        cur = conn.cursor()
        print("Successfully created cursor.")
        return 0
    except Exception as ex:
        print("Could not create cursor. Error: '%s'" % str(ex))
        return -2


# CREATE NEW USER (this may lead to a KeyError if KEY already exists)
def db_create_user(user_id, first_name, last_name, joined_date):
    try:
        postgres_query = """INSERT INTO webbot_users (user_id, first_name, last_name, join_data) VALUES (%s, %s, %s, %s);"""
        query_data = (user_id, first_name, last_name, joined_date)
        cur.execute(postgres_query, query_data)
        conn.commit()
    except Exception as ex:
        db_exc_handler(ex, conn)


# GET LIST OF USER IDS
def db_get_user_ids():
    try:
        postgres_query = """SELECT user_id FROM webbot_users;"""
        cur.execute(postgres_query)
        ids = cur.fetchall()
        return ids  # returns a list of tuples, should be unpacked accordingly in the module that is calling
    except Exception as ex:
        db_exc_handler(ex, conn)


# GET USER INFO
def db_get_user_info(user_id):
    try:
        postgres_query = """SELECT * FROM webbot_users WHERE user_id = %s;"""
        cur.execute(postgres_query, (user_id, ))  # here we have to make the int user_id into a tuple to avoid a TypeError
        user_data = cur.fetchall()
        return user_data[0]  # returns an n-tuple where n is the number of data points (i.e. columns)
    except Exception as ex:
        db_exc_handler(ex, conn)


# DISCONNECT FROM DATABASE
def db_disconnect():
    try:
        conn.close()
        print("Successfully disconnected from database.")
        return 0
    except Exception as ex:
        print("Could not disconnect from database. Error: '%s'" % str(ex))
        return -1
