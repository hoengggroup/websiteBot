# -*- coding: utf-8 -*-

### external libraries
import psycopg2  # for interacting with PostgreSQL databases
import psycopg2.errorcodes  # ...its errorcodes module must be imported seperately

### our own libraries
from loggerService import create_logger


# DATABASE PARAMETERS
my_database = "websitebot_db"
my_user = "websitebot"
my_password = ""
my_host = "localhost"
my_port = "5432"


# logging
logger = create_logger("db")


# Amazing (self-created ;)) error handler
def db_exc_handler(excp, conn):
    logger.error("Error code: " + str(excp.pgcode))
    if (excp.pgcode == psycopg2.errorcodes.CONNECTION_EXCEPTION) or (excp.pgcode == psycopg2.errorcodes.CONNECTION_FAILURE):
        logger.error("Connection error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.DATA_CORRUPTED:
        logger.error("Data corruption error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.DATA_EXCEPTION:
        logger.error("Data error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.DATATYPE_MISMATCH:
        logger.error("Datatype mismatch error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.DATETIME_FIELD_OVERFLOW:
        logger.error("Datetime overflow error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.IN_FAILED_SQL_TRANSACTION:
        logger.error("In failed transaction error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.INTERNAL_ERROR:
        logger.error("Internal error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.IO_ERROR:
        logger.error("IO error. Details: " + str(excp))
    elif (excp.pgcode == psycopg2.errorcodes.NO_DATA) or (excp.pgcode == psycopg2.errorcodes.NO_DATA_FOUND):
        logger.error("No data error. Details: " + str(excp))
    elif (excp.pgcode == psycopg2.errorcodes.NOT_NULL_VIOLATION) or (excp.pgcode == psycopg2.errorcodes.NULL_VALUE_NOT_ALLOWED):
        logger.error("Not null error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.PROHIBITED_SQL_STATEMENT_ATTEMPTED:
        logger.error("Prohibited statement error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.PROTOCOL_VIOLATION:
        logger.error("Protocol violation error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.RAISE_EXCEPTION:
        logger.error("Raise exception error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.RESERVED_NAME:
        logger.error("Reserved name error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.SQL_ROUTINE_EXCEPTION:
        logger.error("Routine exception error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.SQL_STATEMENT_NOT_YET_COMPLETE:
        logger.error("Statement not yet complete error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.SYNTAX_ERROR:
        logger.error("Syntax error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.SYSTEM_ERROR:
        logger.error("System error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.TOO_MANY_ARGUMENTS:
        logger.error("Too many arguments error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.TOO_MANY_COLUMNS:
        logger.error("Too many columns error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.TOO_MANY_ROWS:
        logger.error("Too many rows error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.UNDEFINED_COLUMN:
        logger.error("Undefined column error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.UNDEFINED_OBJECT:
        logger.error("Undefined object error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.UNDEFINED_TABLE:
        logger.error("Undefined table error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.UNIQUE_VIOLATION:
        logger.error("Unique violation error / Key error. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.WARNING:
        logger.error("Warning. Details: " + str(excp))
    elif excp.pgcode == psycopg2.errorcodes.WRONG_OBJECT_TYPE:
        logger.error("Wrong object type error. Details: " + str(excp))
    else:
        logger.error("Unkown error code " + str(excp.pgcode) + ". Lookup: " + psycopg2.errorcodes.lookup(excp.pgcode))


### DATABASE MANAGEMENT
# CONNECT TO DATABASE
def db_connect():
    global conn
    global cur
    try:
        conn = psycopg2.connect(database=my_database, user=my_user, password=my_password, host=my_host, port=my_port)
        conn.set_client_encoding('UNICODE')
        conn.autocommit = False
        logger.info("Successfully connected to database.")
    except Exception as ex:
        logger.error("Could not connect to database. Error: '%s'" % str(ex))
        return False
    try:
        cur = conn.cursor()
        logger.info("Successfully created cursor.")
    except Exception as ex:
        logger.error("Could not create cursor. Error: '%s'" % str(ex))
        return False
    return True


# DISCONNECT FROM DATABASE
def db_disconnect():
    try:
        cur.close()
        logger.info("Successfully closed cursor.")
    except Exception as ex:
        logger.error("Could not close cursor. Error: '%s'" % str(ex))
        return False
    try:
        conn.close()
        logger.info("Successfully disconnected from database.")
    except Exception as ex:
        logger.error("Could not disconnect from database. Error: '%s'" % str(ex))
        return False
    return True


### CREDENTIALS TABLE
# GET BOT TOKEN
def db_credentials_get_bot_token(bot_name):
    try:
        postgres_query = """SELECT token FROM credentials where bot_name = %s;"""
        cur.execute(postgres_query, (bot_name,))  # turn bot_name into a tuple to avoid a TypeError
        token = cur.fetchone()
        if token:
            conn.commit()
            return token[0]  # returns one item (a string)
        else:
            logger.warning("API token for bot \""+str(bot_name)+"\" does not exist.")
            conn.commit()
            return None  # or None if the bot does not exist
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


### USERS TABLE
# CREATE NEW USER
def db_users_create(tg_id, status, first_name, last_name, username, apply_name, apply_text, apply_date):
    try:
        postgres_query = """INSERT INTO users (tg_id, status, first_name, last_name, username, apply_name, apply_text, apply_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"""
        query_data = (tg_id, status, first_name, last_name, username, apply_name, apply_text, apply_date)
        cur.execute(postgres_query, query_data)
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return False
    logger.info("Successfully created user "+str(tg_id)+".")
    conn.commit()
    return True


# DELETE USER
def db_users_delete(tg_id):
    try:
        postgres_query = """DELETE FROM users WHERE tg_id = %s;"""
        cur.execute(postgres_query, (tg_id,))  # turn tg_id into a tuple to avoid a TypeError
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return False
    logger.info("Successfully deleted user "+str(tg_id)+".")
    conn.commit()
    return True


# DOES USER EXIST
def db_users_exists(tg_id):
    try:
        postgres_query = """SELECT EXISTS(SELECT 1 FROM users WHERE tg_id = %s);"""
        cur.execute(postgres_query, (tg_id,))  # turn tg_id into a tuple to avoid a TypeError
        exists = cur.fetchone()
        conn.commit()
        return exists[0]  # returns one item (a boolean)
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# GET LIST OF USER IDS
def db_users_get_all_ids():
    try:
        postgres_query = """SELECT tg_id FROM users;"""
        cur.execute(postgres_query)
        ids = cur.fetchall()
        conn.commit()
        return [item for t in ids for item in t]  # returns a list
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# GET LIST OF ADMINS
def db_users_get_admins():
    try:
        postgres_query = """SELECT tg_id FROM users WHERE status = 0;"""
        cur.execute(postgres_query)
        ids = cur.fetchall()
        conn.commit()
        return [item for t in ids for item in t]  # returns a list
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# GET USER DATA
def db_users_get_data(tg_id, field="all_fields"):
    if not db_users_exists(tg_id):
        logger.debug("users_get_data: User "+str(tg_id)+" does not exist.")
        return None
    # We have to make this clunky if-elif chunk beacuse of protections against SQL injection
    return_list = False
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
            return user_data[0]  # returns one item
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# SET USER DATA
def db_users_set_data(tg_id, field, argument):
    if not db_users_exists(tg_id):
        logger.debug("users_set_data: User "+str(tg_id)+" does not exist.")
        return False
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
        logger.debug("users_set_data: Data field \""+str(field)+"\" does not match any columns. No action taken.")
        return False
    try:
        cur.execute(postgres_query, (argument, tg_id,))  # turn tg_id into a tuple to avoid a TypeError
        logger.info("Successfully changed data field \""+str(field)+"\" in users table to "+str(argument)+".")
        conn.commit()
        return True
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return False


### WEBSITES TABLE
# GET WEBSITE ID
def db_websites_get_id(ws_name):
    try:
        postgres_query = """SELECT ws_id FROM websites WHERE ws_name = %s;"""
        cur.execute(postgres_query, (ws_name,))  # turn ws_name into a tuple to avoid a TypeError
        ws_id = cur.fetchone()
        if ws_id:
            conn.commit()
            return ws_id[0]  # returns one item (an int)
        else:
            logger.debug("websites_get_id: Website \""+str(ws_name)+"\" does not exist.")
            conn.commit()
            return None  # or None if website does not exist
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# GET WEBSITE NAME
def db_websites_get_name(ws_id):
    try:
        postgres_query = """SELECT ws_name FROM websites WHERE ws_id = %s;"""
        cur.execute(postgres_query, (ws_id,))  # turn ws_id into a tuple to avoid a TypeError
        ws_name = cur.fetchone()
        if ws_name:
            conn.commit()
            return ws_name[0]  # returns one item (a string)
        else:
            logger.debug("websites_get_name: Website with ID "+str(ws_id)+" does not exist.")
            conn.commit()
            return None  # or None if website does not exist
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# GET LIST OF WEBSITE IDS
def db_websites_get_all_ids():
    try:
        postgres_query = """SELECT ws_id FROM websites;"""
        cur.execute(postgres_query)
        ids = cur.fetchall()
        conn.commit()
        return [item for t in ids for item in t]  # returns a list
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# ADD WEBSITE
def db_websites_add(ws_name, url, time_sleep, last_time_checked, last_time_updated, last_error_msg, last_error_time, last_hash, last_content):
    try:
        postgres_query = """INSERT INTO websites (ws_name, url, time_sleep, last_time_checked, last_time_updated, last_error_msg, last_error_time, last_hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING ws_id;"""
        query_data = (ws_name, url, time_sleep, last_time_checked, last_time_updated, last_error_msg, last_error_time, last_hash)
        cur.execute(postgres_query, query_data)
        ws_id_1 = cur.fetchone()[0]
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return False
    try:
        postgres_query = """INSERT INTO websites_content (ws_id, update_time, hash, last_content) VALUES (%s, %s, %s, %s) RETURNING ws_id;"""
        query_data = (ws_id_1, last_time_updated, None, last_content)
        cur.execute(postgres_query, query_data)
        ws_id_2 = cur.fetchone()[0]
    except Exception as ex:
        cur.rollback()
        db_exc_handler(ex, conn)
        return False
    if ws_id_1 == ws_id_2:
        logger.info("Successfully created website \""+str(ws_name)+"\".")
        conn.commit()
        return True
    else:
        conn.rollback()
        return False


# REMOVE WEBSITE
def db_websites_remove(ws_name):
    ws_id = db_websites_get_id(ws_name)
    try:
        postgres_query = """DELETE FROM websites WHERE ws_id = %s;"""
        cur.execute(postgres_query, (ws_id,))  # turn ws_id into a tuple to avoid a TypeError
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return False
    logger.info("Successfully deleted website \""+str(ws_name)+"\".")
    conn.commit()
    return True


# GET WEBSITE DATA
def db_websites_get_data(ws_name, field="all_fields"):
    ws_id = db_websites_get_id(ws_name)
    if not ws_id:
        logger.debug("websites_get_data: Website \""+str(ws_name)+"\" does not exist.")
        return None
    # We have to make this clunky if-elif chunk beacuse of protections against SQL injection
    return_list = False
    if field=="url":
        postgres_query = """SELECT url FROM websites WHERE ws_id = %s;"""
    elif field=="time_sleep":
        postgres_query = """SELECT time_sleep FROM websites WHERE ws_id = %s;"""
    elif field=="last_time_checked":
        postgres_query = """SELECT last_time_checked FROM websites WHERE ws_id = %s;"""
    elif field=="last_time_updated":
        postgres_query = """SELECT last_time_updated FROM websites WHERE ws_id = %s;"""
    elif field=="last_error_msg":
        postgres_query = """SELECT last_error_msg FROM websites WHERE ws_id = %s;"""
    elif field=="last_error_time":
        postgres_query = """SELECT last_error_time FROM websites WHERE ws_id = %s;"""
    elif field=="last_hash":
        postgres_query = """SELECT last_hash FROM websites WHERE ws_id = %s;"""
    elif field=="last_content":
        postgres_query = """SELECT last_content FROM websites_content WHERE ws_id = %s;"""
    else:
        # we are only interested in last_content (saved in the websites_content table) in specific cases...
        # ...so we only return it (on its own) if specifically requested with a corresponding "field" argument
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
            return website_data[0]  # returns one item
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# GET WEBSITE CONTENT
def db_websites_get_content(ws_name,ws_hash):
    ws_id = db_websites_get_id(ws_name)
    if not ws_id:
        logger.debug("websites_get_data: Website \""+str(ws_name)+"\" does not exist.")
        return None
    # TODO Prevent here agains sql injections?
    postgres_query = """select last_content from websites_content where ws_id = %s and hash = %s;"""


    try:
        cur.execute(postgres_query, (ws_id,))  # turn ws_id into a tuple to avoid a TypeError
        website_data = cur.fetchall()
        conn.commit()
        return [item for t in website_data for item in t]  # returns a list
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# SET WEBSITE DATA
def db_websites_set_data(ws_name, field, argument):
    ws_id = db_websites_get_id(ws_name)
    if not ws_id:
        logger.debug("websites_set_data: Website \""+str(ws_name)+"\" does not exist.")
        return False
    if field=="ws_name":
        postgres_query = """UPDATE websites SET ws_name = %s WHERE ws_id = %s;"""
    elif field=="url":
        postgres_query = """UPDATE websites SET url = %s WHERE ws_id = %s;"""
    elif field=="time_sleep":
        postgres_query = """UPDATE websites SET time_sleep = %s WHERE ws_id = %s;"""
    elif field=="last_time_checked":
        postgres_query = """UPDATE websites SET last_time_checked = %s WHERE ws_id = %s;"""
    elif field=="last_time_updated":
        postgres_query = """UPDATE websites SET last_time_updated = %s WHERE ws_id = %s;"""
    elif field=="last_error_msg":
        postgres_query = """UPDATE websites SET last_error_msg = %s WHERE ws_id = %s;"""
    elif field=="last_error_time":
        postgres_query = """UPDATE websites SET last_error_time = %s WHERE ws_id = %s;"""
    elif field=="last_hash":
        postgres_query = """UPDATE websites SET last_hash = %s WHERE ws_id = %s;"""
    else:
        logger.debug("websites_set_data: Data field \""+str(field)+"\" does not match any columns. No action taken.")
        return False
    try:
        cur.execute(postgres_query, (argument, ws_id,))  # turn ws_id into a tuple to avoid a TypeError
        if field == "last_content":
            # do not crowd the log with verbatim output of last_content
            logger.info("Successfully changed data field \"last_content\" in websites_content table.")
        else:
            logger.info("Successfully changed data field \""+str(field)+"\" in websites table to "+str(argument)+".")
        conn.commit()
        return True
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return False


# SET WEBSITE DATA CONTENT
def db_websites_set_content_data(ws_name, update_time,hash,content):
    ws_id = db_websites_get_id(ws_name)
    if not ws_id:
        logger.debug("websites_set_data: Website \""+str(ws_name)+"\" does not exist.")
        return False
    postgres_query = """INSERT INTO websites_content (ws_id,update_time, hash,last_content) VALUES (%s,%s,%s,%s) RETURNING ws_id;"""
    query_data = (ws_id, update_time,hash, content)
    try:
        cur.execute(postgres_query, query_data) 
        conn.commit()
        logger.debug("Successfully updated website data content. Ws name: "+str(ws_name))
        return True
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        logger.debug("Error on update website data content. Ws name: "+str(ws_name)+" args hash: "+str(hash))
        return False


### SUBSCIRIPTIONS TABLE
# GET SUBSCRIPTIONS BY WEBSITE
def db_subscriptions_by_website(ws_name):
    ws_id = db_websites_get_id(ws_name)
    if not ws_id:
        logger.debug("subscriptions_by_website: Website \""+str(ws_name)+"\" does not exist.")
        return None
    try:
        postgres_query = """SELECT tg_id FROM subscriptions WHERE ws_id = %s;"""
        cur.execute(postgres_query, (ws_id,))  # turn ws_id into a tuple to avoid a TypeError
        subscribers = cur.fetchall()
        conn.commit()
        return [item for t in subscribers for item in t]  # returns a list
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# GET SUBSCRIPTIONS BY USER
def db_subscriptions_by_user(tg_id):
    if not db_users_exists(tg_id):
        logger.debug("subscriptions_by_user: User "+str(tg_id)+" does not exist.")
        return None
    try:
        postgres_query = """SELECT ws_id FROM subscriptions WHERE tg_id = %s;"""
        cur.execute(postgres_query, (tg_id,))  # turn tg_id into a tuple to avoid a TypeError
        websites_ids = cur.fetchall()
        conn.commit()
        return [item for t in websites_ids for item in t]  # returns a list
    except Exception as ex:
        conn.rollback()
        db_exc_handler(ex, conn)
        return None


# CHECK SPECIFIC SUBSCRIPTION
def db_subscriptions_check(tg_id, ws_id):
    websites_ids = db_subscriptions_by_user(tg_id)
    if not websites_ids:
        return False
    if (ws_id in websites_ids):
        return True
    else:
        return False


# SUBSCRIBE
def db_subscriptions_subscribe(tg_id, ws_name):
    ws_id = db_websites_get_id(ws_name)
    if not ws_id:
        logger.debug("subscriptions_subscribe: Website \""+str(ws_name)+"\" does not exist.")
        return False
    if not db_users_exists(tg_id):
        logger.debug("subscriptions_subscribe: User "+str(tg_id)+" does not exist.")
        return False
    if not db_subscriptions_check(tg_id, ws_id):
        try:
            postgres_query = """INSERT INTO subscriptions (ws_id, tg_id) VALUES (%s, %s);"""
            cur.execute(postgres_query, (ws_id, tg_id))
            logger.info("Successfully subscribed user "+str(tg_id)+" to website \""+str(ws_name)+"\".")
            conn.commit()
            return True
        except Exception as ex:
            conn.rollback()
            db_exc_handler(ex, conn)
            return False
    else:
        logger.debug("User "+str(tg_id)+" was already subscribed to website \""+str(ws_name)+"\". No action taken.")
        return False


# UNSUBSCRIBE
def db_subscriptions_unsubscribe(tg_id, ws_name):
    ws_id = db_websites_get_id(ws_name)
    if not ws_id:
        logger.debug("subscriptions_unsubscribe: Website \""+str(ws_name)+"\" does not exist.")
        return False
    if not db_users_exists(tg_id):
        logger.debug("subscriptions_unsubscribe: User "+str(tg_id)+" does not exist.")
        return False
    if db_subscriptions_check(tg_id, ws_id):
        try:
            postgres_query = """DELETE FROM subscriptions WHERE ws_id = %s AND tg_id = %s;"""
            cur.execute(postgres_query, (ws_id, tg_id))
            logger.info("Successfully unsubscribed user "+str(tg_id)+" from website \""+str(ws_name)+"\".")
            conn.commit()
            return True
        except Exception as ex:
            conn.rollback()
            db_exc_handler(ex, conn)
            return False
    else:
        logger.debug("User "+str(tg_id)+" was already unsubscribed from website \""+str(ws_name)+"\". No action taken.")
        return False
