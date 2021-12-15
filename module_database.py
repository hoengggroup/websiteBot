# -*- coding: utf-8 -*-

# PYTHON BUILTINS
import inspect  # for getting the calling function's name in the error handler

# EXTERNAL LIBRARIES
import psycopg  # for interacting with PostgreSQL databases

# OUR OWN LIBRARIES
from module_config import pg_string
from module_logging import create_logger


# logging
logger = create_logger("db")


# variable initialization
conn = None


# error handler
def db_exc_handler(excp):
    exccode = excp.diag.sqlstate
    exctype = psycopg.errors.lookup(exccode).__name__
    excmsg = excp.diag.message_primary
    excdetail = excp.diag.message_detail
    excfunc = inspect.stack()[1].function
    logger.error("A psycopg {} error has occured in the database module in function {}.\nError code: {}\nError message: {}\nDetails: {}".format(exctype, excfunc, exccode, excmsg, excdetail))


#########################
#  DATABASE MANAGEMENT  #
#########################

# CONNECT TO DATABASE
def db_connect():
    global conn
    try:
        conn = psycopg.connect(pg_string, autocommit=False)
        logger.info("Successfully connected to database.")
        return True
    except Exception as ex:
        logger.error("Could not connect to database. Error: {}".format(ex))
        return False


# DISCONNECT FROM DATABASE
def db_disconnect():
    try:
        conn.close()
        logger.info("Successfully disconnected from database.")
        return True
    except Exception as ex:
        logger.error("Could not disconnect from database. Error: {}".format(ex))
        return False


#########################
#   CREDENTIALS TABLE   #
#########################

# GET BOT TOKEN
def db_credentials_get_bot_token(bot_name):
    with conn.cursor() as cur:
        try:
            postgres_query = """SELECT token FROM credentials where bot_name = %s;"""
            cur.execute(postgres_query, (bot_name,))  # turn bot_name into a tuple to avoid a TypeError
            token = cur.fetchone()
            if token:
                conn.commit()
                return token[0]  # returns one item (a string)
            else:
                logger.warning("API token for bot {} does not exist.".format(bot_name))
                conn.commit()
                return None  # or None if the bot does not exist
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


#########################
#      USERS TABLE      #
#########################

# CREATE NEW USER
def db_users_create(tg_id, status, first_name, last_name, username, apply_name, apply_text, start_time):
    with conn.cursor() as cur:
        try:
            postgres_query = """INSERT INTO users (tg_id, status, first_name, last_name, username, apply_name, apply_text, start_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""
            query_data = (tg_id, status, first_name, last_name, username, apply_name, apply_text, start_time)
            cur.execute(postgres_query, query_data)
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return False
        logger.info("users_create: Successfully created user {}.".format(tg_id))
        conn.commit()
        return True


# DELETE USER
def db_users_delete(tg_id):
    with conn.cursor() as cur:
        try:
            postgres_query = """DELETE FROM users WHERE tg_id = %s;"""
            cur.execute(postgres_query, (tg_id,))  # turn tg_id into a tuple to avoid a TypeError
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return False
        logger.info("users_delete: Successfully deleted user {}.".format(tg_id))
        conn.commit()
        return True


# DOES USER EXIST
def db_users_exists(tg_id):
    with conn.cursor() as cur:
        try:
            postgres_query = """SELECT EXISTS(SELECT 1 FROM users WHERE tg_id = %s);"""
            cur.execute(postgres_query, (tg_id,))  # turn tg_id into a tuple to avoid a TypeError
            exists = cur.fetchone()
            conn.commit()
            return exists[0]  # returns one item (a boolean)
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# GET LIST OF USER IDS
def db_users_get_all_ids():
    with conn.cursor() as cur:
        try:
            postgres_query = """SELECT tg_id FROM users WHERE apply_text IS NOT NULL ORDER BY status, start_time;"""
            cur.execute(postgres_query)
            ids = cur.fetchall()
            conn.commit()
            return [item for t in ids for item in t]  # returns a list
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# GET LIST OF PENDING USER IDS
def db_users_get_all_ids_with_status(status):
    with conn.cursor() as cur:
        try:
            postgres_query = """SELECT tg_id FROM users WHERE apply_text IS NOT NULL AND status = %s ORDER BY start_time;"""
            cur.execute(postgres_query, (status,))  # turn status into a tuple to avoid a TypeError
            ids = cur.fetchall()
            conn.commit()
            return [item for t in ids for item in t]  # returns a list
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# GET LIST OF ADMINS
def db_users_get_admins():
    with conn.cursor() as cur:
        try:
            postgres_query = """SELECT tg_id FROM users WHERE status = 0;"""
            cur.execute(postgres_query)
            ids = cur.fetchall()
            conn.commit()
            return [item for t in ids for item in t]  # returns a list
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# GET USER DATA
def db_users_get_data(tg_id, field="all_fields"):
    with conn.cursor() as cur:
        if not db_users_exists(tg_id):
            logger.debug("users_get_data: User {} does not exist.".format(tg_id))
            return None
        # We have to make this clunky if-elif chunk beacuse of protections against SQL injection
        # This is because SQL statements have to be hardcoded (except for the %s parameters) in order to be protected by psycopg2's escape functions
        # Using standard python string interpolation to modify the field name (which cannot be passed as a parameter to psycopg2) dynamically would thus open us up to injection attacks
        return_list = False
        if field == "status":
            postgres_query = """SELECT status FROM users WHERE tg_id = %s;"""
        elif field == "first_name":
            postgres_query = """SELECT first_name FROM users WHERE tg_id = %s;"""
        elif field == "last_name":
            postgres_query = """SELECT last_name FROM users WHERE tg_id = %s;"""
        elif field == "username":
            postgres_query = """SELECT username FROM users WHERE tg_id = %s;"""
        elif field == "apply_name":
            postgres_query = """SELECT apply_name FROM users WHERE tg_id = %s;"""
        elif field == "apply_text":
            postgres_query = """SELECT apply_text FROM users WHERE tg_id = %s;"""
        elif field == "start_time":
            postgres_query = """SELECT start_time FROM users WHERE tg_id = %s;"""
        else:
            postgres_query = """SELECT * FROM users WHERE tg_id = %s;"""
            return_list = True
        try:
            cur.execute(postgres_query, (tg_id,))  # turn tg_id into a tuple to avoid a TypeError
            if return_list:
                user_data = cur.fetchall()
                conn.commit()
                return [item for t in user_data for item in t]  # returns a list
            else:
                user_data = cur.fetchone()
                conn.commit()
                if user_data:
                    return user_data[0]  # returns one item
                else:
                    return None  # or None if the data does not exist
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# SET USER DATA
def db_users_set_data(tg_id, field, argument):
    with conn.cursor() as cur:
        if not db_users_exists(tg_id):
            logger.debug("users_set_data: User {} does not exist.".format(tg_id))
            return False
        if field == "status":
            postgres_query = """UPDATE users SET status = %s WHERE tg_id = %s;"""
        elif field == "first_name":
            postgres_query = """UPDATE users SET first_name = %s WHERE tg_id = %s;"""
        elif field == "last_name":
            postgres_query = """UPDATE users SET last_name = %s WHERE tg_id = %s;"""
        elif field == "username":
            postgres_query = """UPDATE users SET username = %s WHERE tg_id = %s;"""
        elif field == "apply_name":
            postgres_query = """UPDATE users SET apply_name = %s WHERE tg_id = %s;"""
        elif field == "apply_text":
            postgres_query = """UPDATE users SET apply_text = %s WHERE tg_id = %s;"""
        elif field == "start_time":
            postgres_query = """UPDATE users SET start_time = %s WHERE tg_id = %s;"""
        else:
            logger.debug("users_set_data: Data field {} does not match any columns. No action taken.".format(field))
            return False
        try:
            cur.execute(postgres_query, (argument, tg_id))
            logger.info("users_set_data: Successfully changed data field {} in users table to {} for user {}.".format(field, argument, tg_id))
            conn.commit()
            return True
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return False


#########################
#    WEBSITES TABLE     #
#########################

# GET WEBSITE ID
def db_websites_get_id(ws_name):
    with conn.cursor() as cur:
        try:
            postgres_query = """SELECT ws_id FROM websites WHERE ws_name = %s;"""
            cur.execute(postgres_query, (ws_name,))  # turn ws_name into a tuple to avoid a TypeError
            ws_id = cur.fetchone()
            if ws_id:
                conn.commit()
                return ws_id[0]  # returns one item (an int)
            else:
                logger.debug("websites_get_id: Website {} does not exist.".format(ws_name))
                conn.commit()
                return None  # or None if website does not exist
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# GET WEBSITE NAME
def db_websites_get_name(ws_id):
    with conn.cursor() as cur:
        try:
            postgres_query = """SELECT ws_name FROM websites WHERE ws_id = %s;"""
            cur.execute(postgres_query, (ws_id,))  # turn ws_id into a tuple to avoid a TypeError
            ws_name = cur.fetchone()
            if ws_name:
                conn.commit()
                return ws_name[0]  # returns one item (a string)
            else:
                logger.debug("websites_get_name: Website with ID {} does not exist.".format(ws_id))
                conn.commit()
                return None  # or None if website does not exist
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# GET LIST OF WEBSITE IDS
def db_websites_get_all_ids():
    with conn.cursor() as cur:
        try:
            postgres_query = """SELECT ws_id FROM websites ORDER BY ws_name;"""
            cur.execute(postgres_query)
            ids = cur.fetchall()
            conn.commit()
            return [item for t in ids for item in t]  # returns a list
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# ADD WEBSITE
def db_websites_add(ws_name, url, time_sleep, last_time_checked, last_time_updated, last_error_msg, last_error_time, last_hash, last_content, filters):
    with conn.cursor() as cur:
        # sanity check for type conversions: passing a NoneType as website name should produce an empty response in all functions, not a hit on a website named "None"
        # ...so this name will be reserved just in case
        if ws_name.lower() == "none":
            return False
        try:
            postgres_query = """INSERT INTO websites (ws_name, url, time_sleep, last_time_checked, last_time_updated, last_error_msg, last_error_time, last_hash, filters) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING ws_id;"""
            query_data = (ws_name, url, time_sleep, last_time_checked, last_time_updated, last_error_msg, last_error_time, last_hash, filters)
            cur.execute(postgres_query, query_data)
            ws_id_1 = cur.fetchone()[0]
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return False
        try:
            postgres_query = """INSERT INTO websites_content (ws_id, last_time_updated, last_hash, last_content) VALUES (%s, %s, %s, %s) RETURNING ws_id;"""
            query_data = (ws_id_1, last_time_updated, last_hash, last_content)
            cur.execute(postgres_query, query_data)
            ws_id_2 = cur.fetchone()[0]
        except psycopg.Error as ex:
            cur.rollback()
            db_exc_handler(ex)
            return False
        if ws_id_1 == ws_id_2:
            logger.info("websites_add: Successfully created website {}.".format(ws_name))
            conn.commit()
            return True
        else:
            conn.rollback()
            return False


# REMOVE WEBSITE
def db_websites_remove(ws_name):
    with conn.cursor() as cur:
        ws_id = db_websites_get_id(ws_name)
        if not ws_id:
            logger.debug("websites_remove: Website {} does not exist.".format(ws_name))
            return False
        try:
            postgres_query = """DELETE FROM websites WHERE ws_id = %s;"""
            cur.execute(postgres_query, (ws_id,))  # turn ws_id into a tuple to avoid a TypeError
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return False
        logger.info("websites_remove: Successfully deleted website {}.".format(ws_name))
        conn.commit()
        return True


# GET WEBSITE DATA
def db_websites_get_data(ws_name, field="all_fields"):
    with conn.cursor() as cur:
        ws_id = db_websites_get_id(ws_name)
        if not ws_id:
            logger.debug("websites_get_data: Website {} does not exist.".format(ws_name))
            return None
        # We have to make this clunky if-elif chunk beacuse of protections against SQL injection
        # This is because SQL statements have to be hardcoded (except for the %s parameters) in order to be protected by psycopg2's escape functions
        # Using standard python string interpolation to modify the field name (which cannot be passed as a parameter to psycopg2) dynamically would thus open us up to injection attacks
        return_list = False
        if field == "url":
            postgres_query = """SELECT url FROM websites WHERE ws_id = %s;"""
        elif field == "time_sleep":
            postgres_query = """SELECT time_sleep FROM websites WHERE ws_id = %s;"""
        elif field == "last_time_checked":
            postgres_query = """SELECT last_time_checked FROM websites WHERE ws_id = %s;"""
        elif field == "last_time_updated":
            postgres_query = """SELECT last_time_updated FROM websites WHERE ws_id = %s;"""
        elif field == "last_error_msg":
            postgres_query = """SELECT last_error_msg FROM websites WHERE ws_id = %s;"""
        elif field == "last_error_time":
            postgres_query = """SELECT last_error_time FROM websites WHERE ws_id = %s;"""
        elif field == "last_hash":
            postgres_query = """SELECT last_hash FROM websites WHERE ws_id = %s;"""
        elif field == "filters":
            postgres_query = """SELECT filters FROM websites WHERE ws_id = %s;"""
        else:
            postgres_query = """SELECT * FROM websites WHERE ws_id = %s;"""
            return_list = True
        try:
            cur.execute(postgres_query, (ws_id,))  # turn ws_id into a tuple to avoid a TypeError
            if return_list:
                website_data = cur.fetchall()
                conn.commit()
                return [item for t in website_data for item in t]  # returns a list
            else:
                website_data = cur.fetchone()
                conn.commit()
                if website_data:
                    return website_data[0]  # returns one item
                else:
                    return None  # or None if the data does not exist
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# GET WEBSITE CONTENT
def db_websites_get_content(ws_name, last_time_updated, last_hash):
    with conn.cursor() as cur:
        ws_id = db_websites_get_id(ws_name)
        if not ws_id:
            logger.debug("websites_get_content: Website {} does not exist.".format(ws_name))
            return None
        postgres_query = """SELECT last_content FROM websites_content WHERE ws_id = %s AND last_time_updated = %s AND last_hash = %s;"""
        query_data = (ws_id, last_time_updated, last_hash)
        try:
            cur.execute(postgres_query, query_data)
            website_content = cur.fetchone()
            conn.commit()
            if website_content:
                return website_content[0]  # returns one item
            else:
                return None  # or None if the data does not exist
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# SET WEBSITE DATA
def db_websites_set_data(ws_name, field, argument):
    with conn.cursor() as cur:
        ws_id = db_websites_get_id(ws_name)
        if not ws_id:
            logger.debug("websites_set_data: Website {} does not exist.".format(ws_name))
            return False
        if field == "ws_name":
            postgres_query = """UPDATE websites SET ws_name = %s WHERE ws_id = %s;"""
        elif field == "url":
            postgres_query = """UPDATE websites SET url = %s WHERE ws_id = %s;"""
        elif field == "time_sleep":
            postgres_query = """UPDATE websites SET time_sleep = %s WHERE ws_id = %s;"""
        elif field == "last_time_checked":
            postgres_query = """UPDATE websites SET last_time_checked = %s WHERE ws_id = %s;"""
        elif field == "last_time_updated":
            postgres_query = """UPDATE websites SET last_time_updated = %s WHERE ws_id = %s;"""
        elif field == "last_error_msg":
            postgres_query = """UPDATE websites SET last_error_msg = %s WHERE ws_id = %s;"""
        elif field == "last_error_time":
            postgres_query = """UPDATE websites SET last_error_time = %s WHERE ws_id = %s;"""
        elif field == "last_hash":
            postgres_query = """UPDATE websites SET last_hash = %s WHERE ws_id = %s;"""
        elif field == "filters":
            postgres_query = """UPDATE websites SET filters = %s WHERE ws_id = %s;"""
        else:
            logger.debug("websites_set_data: Data field {} does not match any columns. No action taken.".format(field))
            return False
        try:
            cur.execute(postgres_query, (argument, ws_id))
            logger.info("websites_set_data: Successfully changed data field {} in websites table to {} for website {}.".format(field, argument, ws_name))
            conn.commit()
            return True
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return False


# ADD WEBSITE CONTENT
def db_websites_add_content(ws_name, last_time_updated, last_hash, last_content):
    with conn.cursor() as cur:
        ws_id = db_websites_get_id(ws_name)
        if not ws_id:
            logger.debug("websites_add_content: Website {} does not exist.".format(ws_name))
            return False
        postgres_query = """INSERT INTO websites_content (ws_id, last_time_updated, last_hash, last_content) VALUES (%s, %s, %s, %s) RETURNING ws_id;"""
        query_data = (ws_id, last_time_updated, last_hash, last_content)
        try:
            cur.execute(postgres_query, query_data)
            logger.info("websites_add_content: Successfully added website content for website {}.".format(ws_name))
            conn.commit()
            return True
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return False


# DELETE WEBSITE CONTENT
def db_websites_delete_content(ws_name):
    with conn.cursor() as cur:
        ws_id = db_websites_get_id(ws_name)
        if not ws_id:
            logger.debug("websites_delete_content: Website {} does not exist.".format(ws_name))
            return False
        postgres_query = """DELETE FROM websites_content WHERE ws_id = %s;"""
        try:
            cur.execute(postgres_query, (ws_id,))  # turn ws_id into a tuple to avoid a TypeError
            logger.info("websites_delete_content: Successfully removed all previous website content for website {}.".format(ws_name))
            conn.commit()
            return True
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return False


#########################
# SUBSCIRIPTIONS TABLE  #
#########################

# GET SUBSCRIPTIONS BY WEBSITE
def db_subscriptions_by_website(ws_name):
    with conn.cursor() as cur:
        ws_id = db_websites_get_id(ws_name)
        if not ws_id:
            logger.debug("subscriptions_by_website: Website {} does not exist.".format(ws_name))
            return None
        try:
            postgres_query = """SELECT tg_id FROM subscriptions WHERE ws_id = %s ORDER BY tg_id;"""
            cur.execute(postgres_query, (ws_id,))  # turn ws_id into a tuple to avoid a TypeError
            subscribers = cur.fetchall()
            conn.commit()
            return [item for t in subscribers for item in t]  # returns a list
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# GET SUBSCRIPTIONS BY USER
def db_subscriptions_by_user(tg_id):
    with conn.cursor() as cur:
        if not db_users_exists(tg_id):
            logger.debug("subscriptions_by_user: User {} does not exist.".format(tg_id))
            return None
        try:
            postgres_query = """SELECT ws_id FROM subscriptions WHERE tg_id = %s ORDER BY ws_id;"""
            cur.execute(postgres_query, (tg_id,))  # turn tg_id into a tuple to avoid a TypeError
            websites_ids = cur.fetchall()
            conn.commit()
            return [item for t in websites_ids for item in t]  # returns a list
        except psycopg.Error as ex:
            conn.rollback()
            db_exc_handler(ex)
            return None


# CHECK SPECIFIC SUBSCRIPTION
def db_subscriptions_check(tg_id, ws_id):
    websites_ids = db_subscriptions_by_user(tg_id)
    if not websites_ids:
        return False
    if ws_id in websites_ids:
        return True
    else:
        return False


# SUBSCRIBE
def db_subscriptions_subscribe(tg_id, ws_name):
    with conn.cursor() as cur:
        ws_id = db_websites_get_id(ws_name)
        if not ws_id:
            logger.debug("subscriptions_subscribe: Website {} does not exist.".format(ws_name))
            return False
        if not db_users_exists(tg_id):
            logger.debug("subscriptions_subscribe: User {} does not exist.".format(tg_id))
            return False
        if not db_subscriptions_check(tg_id, ws_id):
            try:
                postgres_query = """INSERT INTO subscriptions (ws_id, tg_id) VALUES (%s, %s);"""
                cur.execute(postgres_query, (ws_id, tg_id))
                logger.info("subscriptions_subscribe: Successfully subscribed user {} to website {}.".format(tg_id, ws_name))
                conn.commit()
                return True
            except psycopg.Error as ex:
                conn.rollback()
                db_exc_handler(ex)
                return False
        else:
            logger.debug("subscriptions_subscribe: User {} was already subscribed to website {}. No action taken.".format(tg_id, ws_name))
            return False


# UNSUBSCRIBE
def db_subscriptions_unsubscribe(tg_id, ws_name):
    with conn.cursor() as cur:
        ws_id = db_websites_get_id(ws_name)
        if not ws_id:
            logger.debug("subscriptions_unsubscribe: Website {} does not exist.".format(ws_name))
            return False
        if not db_users_exists(tg_id):
            logger.debug("subscriptions_unsubscribe: User {} does not exist.".format(tg_id))
            return False
        if db_subscriptions_check(tg_id, ws_id):
            try:
                postgres_query = """DELETE FROM subscriptions WHERE ws_id = %s AND tg_id = %s;"""
                cur.execute(postgres_query, (ws_id, tg_id))
                logger.info("subscriptions_unsubscribe: Successfully unsubscribed user {} from website {}.".format(tg_id, ws_name))
                conn.commit()
                return True
            except psycopg.Error as ex:
                conn.rollback()
                db_exc_handler(ex)
                return False
        else:
            logger.debug("subscriptions_unsubscribe: User {} was already unsubscribed from website {}. No action taken.".format(tg_id, ws_name))
            return False
