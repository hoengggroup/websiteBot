#!/usr/bin/env python3
import sqlite3

import datetime
import pickle  # for saving dicts to file



class Webpage:
    def __init__(self, url, t_sleep):
        self.url = url
        self.t_sleep = t_sleep  # sleeping time in seconds
        self.last_time_checked = datetime.datetime.min  # init with minimal datetime value (year 1 AD)
        self.last_time_changed = datetime.datetime.min  # init with minimal datetime value (year 1 AD)
        self.last_error_msg = ""

        self.chat_ids = set()

        # used while running
        self.last_hash = ""
        self.last_content = ""

    def __str__(self):
        return ("URL: " + str(self.url) + "\n"
                "Sleep timer: " + str(self.t_sleep) + "\n"
                "Last time checked: " + str(self.last_time_checked) + "\n"
                "Last time changed: " + str(self.last_time_changed) + "\n"
                "Last error message: " + str(self.last_error_msg) + "\n"
                "Chat IDs: " + str(self.chat_ids))

    def get_url(self):
        return self.url

    def get_t_sleep(self):
        return self.t_sleep

    def set_t_sleep(self, new_t_sleep):
        self.t_sleep = new_t_sleep
        logger.info("Set new t_sleep for \"" + str(self.url) + "\" to " + str(self.t_sleep) + " seconds.")

    def get_last_time_checked(self):
        return self.last_time_checked

    def update_last_time_checked(self):
        self.last_time_checked = datetime.datetime.now()

    def get_chat_ids(self):
        return self.chat_ids

    def is_chat_id_active(self, chat_id_to_check):
        if chat_id_to_check in self.chat_ids:
            return True
        else:
            return False

    def add_chat_id(self, chat_id_to_add):
        if chat_id_to_add in self.chat_ids:
            logger.info("Chat ID " + str(chat_id_to_add) + " is already subscribed to \"" + str(self.url) + "\".")
            return False
        try:
            self.chat_ids.add(chat_id_to_add)
            logger.info("Added chat ID " + str(chat_id_to_add) + " to \"" + str(self.url) + "\".")
            return True
        except KeyError:
            logger.error("Failed to add chat ID " + str(chat_id_to_add) + " to: \"" + str(self.url) + "\".")
            return False

    def remove_chat_id(self, chat_id_to_remove):
        if chat_id_to_remove not in self.chat_ids:
            logger.info("Chat ID " + str(chat_id_to_remove) + " is already unsubscribed from \"" + str(self.url) + "\".")
            return False
        try:
            self.chat_ids.remove(chat_id_to_remove)
            logger.info("Removed chat ID " + str(chat_id_to_remove) + " from \"" + str(self.url) + "\".")
            return True
        except KeyError:
            logger.error("Failed to remove chat ID " + str(chat_id_to_remove) + " from \"" + str(self.url) + "\".")
            return False

    def get_last_hash(self):
        return self.last_hash

    def get_last_content(self):
        return self.last_content

    def update_last_content(self, new_last_content):
        new_last_hash = (hashlib.md5(new_last_content.encode())).hexdigest()
        print("New last hash: " + str(new_last_hash))
        if self.last_hash != new_last_hash:
            self.last_time_changed = datetime.datetime.now()
            print("Really updated last hash.")
        self.last_hash = new_last_hash
        print("Updated last hash: " + str(self.get_last_hash()))
        self.last_content = new_last_content

class ChatID:
    def __init__(self, status, user_data):
        self.status = status  # 0 = admin, 1 = user, 2 = pending, 3 = denied
        self.user_data = None
        self.apply_name = ""
        self.apply_message = ""

    def get_status(self):
        return self.status

    def set_status(self, new_status):
        try:
            new_status = int(new_status)
            if self.status != new_status:
                self.status = new_status
                logger.info("Set new status " + str(new_status) + " for this chat ID.")
                return True
            else:
                logger.warning("The status " + str(new_status) + " is already the current status of this chat ID.")
                return False
        except KeyError:
            logger.error("Failed to set new status " + str(new_status) + " for this chat ID.")
            return False

    def get_user_data(self):
        return self.user_data

    def set_user_data(self, new_user_data):
        try:
            self.user_data = new_user_data
            logger.info("Set new user data " + str(new_user_data) + " for this chat ID.")
            return True
        except KeyError:
            logger.error("Failed to set new user data " + str(new_user_data) + " for this chat ID.")
            return False

    def get_apply_name(self):
        return self.apply_name

    def set_apply_name(self, new_apply_name):
        try:
            self.apply_name = new_apply_name
            logger.info("Set new apply name " + str(new_apply_name) + " for this chat ID.")
            return True
        except KeyError:
            logger.error("Failed to set new apply name " + str(new_apply_name) + " for this chat ID.")
            return False

    def get_apply_message(self):
        return self.apply_message

    def set_apply_message(self, new_apply_message):
        try:
            self.apply_message = new_apply_message
            logger.info("Set new apply message " + str(new_apply_message) + " for this chat ID.")
            return True
        except KeyError:
            logger.error("Failed to set new apply message " + str(new_apply_message) + " for this chat ID.")
            return False


global webpages_dict
with open('webpages.pickle', 'rb') as handle:
    webpages_dict = pickle.load(handle)

for element in webpages_dict:
    print(element)



conn = sqlite3.connect('my_database.sqlite',detect_types=sqlite3.PARSE_DECLTYPES |
                                           sqlite3.PARSE_COLNAMES) # those types to detect e.g. datetime
cursor = conn.cursor()
"""cursor.execute('''CREATE TABLE TABLE1
        (NAME text PRIMARY KEY     NOT NULL,
         URL           text    NOT NULL,
         T_SLEEP            int     NOT NULL,
         LAST_TIME_CHECKED        DATETYPE,
         LAST_ERROR_MSG          text);''')"""
"""cursor = conn.cursor()"""

sql_insert_with_params = """INSERT INTO TABLE1
                          (NAME,URL,T_SLEEP,LAST_TIME_CHECKED,LAST_ERROR_MSG)) 
                          VALUES (?, ?, ?,?,?);"""
#now =  datetime.datetime.now()
dataTuple = ("myWebsite","myUrl",30,0,"404 $=$ error")

#cursor.execute(sql_insert_with_params,("myWebsite","myUrl",30,0,"404 $=$ error"))
cursor.execute("SELECT * from ? WHERE name = ?", ("a", "b"))

conn.commit()

"""
cursor.execute("INSERT INTO SCHOOL (ID,NAME,AGE,ADDRESS,MARKS) \
      VALUES (20, 'Allen', 14, 'Bangalore', 150 )");
cursor.execute("INSERT INTO SCHOOL (ID,NAME,AGE,ADDRESS,MARKS) \
      VALUES (30, 'Martha', 15, 'Hyderabad', 200 )");
cursor.execute("INSERT INTO SCHOOL (ID,NAME,AGE,ADDRESS,MARKS) \
      VALUES (40, 'Palak', 15, 'Kolkata', 650)");conn.commit()
cursor.close()"""
for row in cursor.execute("SELECT id, name, marks from STRING_KEYS"):
    print("ID = ", row[0])
    print("NAME = ", row[1])
    print("MARKS = ", row[2], "\n")

cursor.execute("SELECT * FROM STRING_KEYS")
print(cursor.fetchall())

print("Opened database successfully")