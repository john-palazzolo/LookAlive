import sqlite3
import time


def __open_database():
    # This function connects to and returns the database object
    conn = sqlite3.connect('lookalive/databases/pm.db')
    c = conn.cursor()

    return conn, c


def send_message(to_uuid, from_uuid, message):
    conn, c = __open_database()

    c.execute("INSERT INTO pm VALUES (?, ?, ?, ?, ?, ?)", (to_uuid, from_uuid, get_id(), message, time.time(), str([to_uuid, from_uuid])))

    conn.commit()
    c.close()
    conn.close()


def see_messages(uuid_1, uuid_2):

    conn, c = __open_database()

    messages = get_messages(uuid_1, uuid_2)

    for message in messages:
        seen = eval(message[5])
        for user in range(len(seen)):
            seen[user] = int(seen[user])
        try:
            seen.remove(int(uuid_1))
            c.execute('UPDATE pm SET seen_by = ? WHERE id = ?', (str(seen), message[2],))
        except ValueError:
            pass

    conn.commit()
    c.close()
    conn.close()


def get_unseen_messages(uuid):
    conn, c = __open_database()

    c.execute("SELECT * FROM pm")
    unseen = 0

    all_messages = c.fetchall()

    for message in all_messages:
        if int(uuid) in eval(message[5]):
            unseen += 1

    return unseen


def get_people_unseen_messages(uuid, uuid_2):
    conn, c = __open_database()

    c.execute('SELECT * FROM pm WHERE to_uuid=? AND from_uuid=? ', (uuid, uuid_2))
    unseen = 0

    all_messages = c.fetchall()

    c.execute('SELECT * FROM pm WHERE from_uuid=? AND to_uuid=? ', (uuid, uuid_2))

    all_messages + c.fetchall()

    for message in all_messages:
        if int(uuid) in eval(message[5]):
            unseen += 1

    return unseen


def get_messages(uuid_1, uuid_2):
    uuid_1 = str(uuid_1)
    uuid_2 = str(uuid_2)
    conn, c = __open_database()

    c.execute("SELECT * FROM pm WHERE to_uuid=? AND from_uuid=?", (uuid_1, uuid_2,))
    to_from = c.fetchall()

    c.execute("SELECT * FROM pm WHERE to_uuid=? AND from_uuid=?", (uuid_2, uuid_1,))
    from_to = c.fetchall()

    result = to_from + from_to

    result = sorted(result, key = lambda x: float(x[4]))

    return result


def get_id():
    conn, c = __open_database()
    c.execute('SELECT * FROM pm')

    all_accounts = c.fetchall()

    uuid = []

    for item in all_accounts:
        uuid.append(item[2])

    try:
        uuid = max(uuid) + 1
    except TypeError:
        uuid = 0
    except ValueError:
        uuid = 0
    return uuid


def delete_message(message_id):

    conn, c = __open_database()

    c.execute("DELETE FROM pm WHERE id=?", (message_id,))

    conn.commit()
    c.close()
    conn.close()


def get_number_private_messages():
    conn, c = __open_database()
    c.execute("SELECT * FROM pm")
    return len(c.fetchall())

