import things
import users

import datetime

LOG_FILE = 'lookalive/security/log.txt'

def read_log():
    return things.read_file(LOG_FILE)

def write_log(uuid, action):
    current = read_log()

    time = datetime.datetime.now()
    entry = "[{}] ({} - {}) : {}".format(time, users.get_username(int(uuid)), int(uuid), str(action))

    current.insert(0, entry)

    things.write_list_to_file(LOG_FILE, current)


def write_log_control(action):
    current = read_log()

    time = datetime.datetime.now()
    entry = "[{}] : {}".format(time, str(action))

    current.insert(0, entry)

    things.write_list_to_file(LOG_FILE, current)


def breaker(character):
    current = read_log()

    entry = character * 64

    current.insert(0, entry)

    things.write_list_to_file(LOG_FILE, current)


def clear_log():
    things.clear_file(LOG_FILE)