#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
from psycopg2 import errorcodes


# DATABASE PARAMETERS
my_database = "websitebot_db"
my_user = "websitebot"
my_password = ""
my_host = "localhost"
my_port = "5432"


# Amazing (self-created ;)) error handler.
# Common errors should be added following the pattern of the UNIQUE_VIOLATION error.
def db_exc_handler(excp, conn):
    print("Error: " + str(excp.pgcode))
    if excp.pgcode == errorcodes.UNIQUE_VIOLATION:
        print("Key error. Details: " + str(excp))
        conn.rollback()
    else:
        print("Unkown error " + str(excp.pgcode) + " Lookup: " + errorcodes.lookup(excp.pgcode))


### DATABASE MANAGEMENT
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


# DISCONNECT FROM DATABASE
def db_disconnect():
    try:
        cur.close()
        conn.close()
        print("Successfully disconnected from database.")
        return 0
    except Exception as ex:
        print("Could not disconnect from database. Error: '%s'" % str(ex))
        return -1


### USER TABLE
# CREATE NEW USER
def db_create_user(tg_id, status, first_name, last_name, username, apply_name, apply_text, apply_date):
    try:
        postgres_query = """INSERT INTO users (tg_id, status, first_name, last_name, username, apply_name, apply_text, apply_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""
        query_data = (tg_id, status, first_name, last_name, username, apply_name, apply_text, apply_date)
        cur.execute(postgres_query, query_data)
        conn.commit()
    except Exception as ex:
        db_exc_handler(ex, conn)


# DELETE USER
def db_delete_user(tg_id):
    try:
        postgres_query = """DELETE FROM users WHERE tg_id = %s;"""
        cur.execute(postgres_query, (tg_id,))
        conn.commit()
    except Exception as ex:
        db_exc_handler(ex, conn)


# GET LIST OF USER IDS
def db_get_user_ids():
    try:
        postgres_query = """SELECT tg_id FROM users;"""
        cur.execute(postgres_query)
        ids = cur.fetchall()
        return ids  # returns a list of tuples, should be unpacked accordingly in the module that is calling
    except Exception as ex:
        db_exc_handler(ex, conn)


# GET USER DATA
def db_get_user_data(tg_id, field="all_fields"):
    # We have to make this clunky if-elif chunk beacuse of protections against SQL injection
    if field=="status":
        postgres_query = """SELECT status FROM users WHERE tg_id = %s;"""
    elif field=="first_name":
        postgres_query = """SELECT first_name FROM users WHERE tg_id = %s;"""
    elif field=="last_name":
        postgres_query = """SELECT last_name FROM users WHERE tg_id = %s;"""
    elif field=="username":
        postgres_query = """SELECT username FROM users WHERE tg_id = %s;"""
    elif field=="apply_name":
        postgres_query = """SELECT apply_name FROM users WHERE tg_id = %s;"""
    elif field=="apply_text":
        postgres_query = """SELECT apply_text FROM users WHERE tg_id = %s;"""
    elif field=="apply_date":
        postgres_query = """SELECT apply_date FROM users WHERE tg_id = %s;"""
    else:
        postgres_query = """SELECT * FROM users WHERE tg_id = %s;"""
    try:
        cur.execute(postgres_query, (tg_id,))  # here we have to make the int tg_id into a tuple to avoid a TypeError
        user_data = cur.fetchall()
        return user_data[0]  # returns an n-tuple where n is the number of data points (i.e. columns)
    except Exception as ex:
        db_exc_handler(ex, conn)


# SET USER DATA
def db_set_user_data(tg_id, field, argument):
    if field=="status":
        postgres_query = """UPDATE users SET status = %s WHERE tg_id = %s;"""
    elif field=="first_name":
        postgres_query = """UPDATE users SET first_name = %s WHERE tg_id = %s;"""
    elif field=="last_name":
        postgres_query = """UPDATE users SET last_name = %s WHERE tg_id = %s;"""
    elif field=="username":
        postgres_query = """UPDATE users SET username = %s WHERE tg_id = %s;"""
    elif field=="apply_name":
        postgres_query = """UPDATE users SET apply_name = %s WHERE tg_id = %s;"""
    elif field=="apply_text":
        postgres_query = """UPDATE users SET apply_text = %s WHERE tg_id = %s;"""
    elif field=="apply_date":
        postgres_query = """UPDATE users SET apply_date = %s WHERE tg_id = %s;"""
    else:
        print("Incorrect data field given, no action taken.")
        return
    try:
        cur.execute(postgres_query, (argument, tg_id,))  # here we have to make the int tg_id into a tuple to avoid a TypeError
        conn.commit()
        return
    except Exception as ex:
        db_exc_handler(ex, conn)
