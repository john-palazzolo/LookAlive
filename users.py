import sqlite3
import notification
import os
import message
import comment
import hash
import config
from builtin import *


def __open_database():
    # This function connects to and returns the database object
    try:
        conn = sqlite3.connect('lookalive/databases/users.db')
    except sqlite3.OperationalError:
        conn = sqlite3.connect('databases/users.db')
    c = conn.cursor()

    return conn, c


def new_user(display, user, password, email):
    conn, c = __open_database()

    uuid = get_uuid()

    notification.new_user(uuid)

    password = hash_password(password)

    c.execute("INSERT INTO users (display, username, password, following, followers, email, uuid) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (display, user, password, '[]', '[]', email, uuid))

    conn.commit()
    c.close()
    conn.close()

    follow(uuid, 15, False)
    follow(uuid, 1, False)
    follow(uuid, 0, False)
    comment.like_post(uuid, 0)



def username_verify(username):
    conn, c = __open_database()

    c.execute('SELECT * FROM users WHERE username=?', (username,))

    if len(c.fetchall()) > 0:
        return False
    else:
        return True


def get_uuid():
    conn, c = __open_database()
    c.execute('SELECT * FROM users')

    all_accounts = c.fetchall()

    uuid = []

    for item in all_accounts:
        uuid.append(item[6])

    try:
        uuid = max(uuid) + 1
    except TypeError:
        uuid = 0
    except ValueError:
        uuid = 0
    return uuid


def get_password(uuid):
    conn, c = __open_database()
    c.execute('SELECT password FROM users WHERE uuid=?', (uuid,))

    password = c.fetchall()
    output(password)
    output("fjeyfgj")
    return str(password[0])

def hash_password(password):
    return hash.hash_string(password)


def get_user_uuid(user):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE username=?', (user,))
    uuid = c.fetchall()[0]
    return uuid[6]


def get_username(uuid, value=0):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))
    user = c.fetchall()[0]
    return user[value]


def get_info(username):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    try:
        data = c.fetchall()[0]
    except IndexError:
        return None
    return data


def get_info_uuid(uuid):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))
    try:
        data = c.fetchall()[0]
    except IndexError:
        return None
    return data


def get_info_raw(username):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    return c.fetchall()


def get_info_raw_uuid(uuid):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))
    return c.fetchall()


def get_user_name(uuid):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))
    uuid = c.fetchall()[0]
    uuid = uuid[1]
    return uuid


def login(username, password, hashed=False):
    if hashed is False:
        password = hash_password(password)
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    try:
        passw = c.fetchall()[0]

        if str(password) == str(passw[2]):
            return True
        else:
            return False
    except IndexError:
        return False


def update_user(display, user, email, password, old_password, old_user):
    conn, c = __open_database()

    # print display, user, email, password, old_password, old_user

    if display != '':
        c.execute('UPDATE users SET display = ? WHERE username = ?', (display, old_user,))

    if email != '':
        c.execute('UPDATE users SET email = ? WHERE username = ?', (email, old_user,))

    if password != '':
        c.execute('UPDATE users SET password = ? WHERE username = ?', (hash_password(password), old_user,))

    if user != '':
        c.execute('SELECT * FROM users')
        users = c.fetchall()
        # No Repeater Usernames
        for item in users:
            if item[1] == user:
                return False
        c.execute('UPDATE users SET username = ? WHERE username = ?', (user, old_user,))

    conn.commit()
    c.close()
    conn.close()


def follow(uuid, follower_uuid, notify=True, toggle_mode=True):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))

    users = c.fetchall()[0]
    users = eval(users[3])

    if int(follower_uuid) not in users:
        if notify is True:
            notification.add_notification(uuid, 'You Are Now Following {}!'.format(get_username(follower_uuid)), follower_uuid)
            notification.add_notification(follower_uuid, '{} Is Now Follwing You!'.format(get_username(uuid)), uuid)

        users.append(int(follower_uuid))
        users = str(users)

        c.execute('UPDATE users SET following = ? WHERE uuid = ?', (users, uuid,))

        # ==============================================================================================

        c.execute('SELECT * FROM users WHERE uuid=?', (follower_uuid,))

        try:
            users = c.fetchall()[0]
            users = eval(users[4])
            users.append(int(uuid))
            users = str(users)

            c.execute('UPDATE users SET followers = ? WHERE uuid = ?', (users, follower_uuid,))
        except IndexError:
            pass

        conn.commit()
        c.close()
        conn.close()


    else:
        if toggle_mode is True:
            if notify is True:
                notification.add_notification(uuid, 'You Are No Longer Following {}!'.format(get_username(follower_uuid)), follower_uuid)
                notification.add_notification(follower_uuid, '{} Is No Longer Follwing You!'.format(get_username(uuid)), uuid)

            users.remove(int(follower_uuid))
            users = str(users)

            c.execute('UPDATE users SET following = ? WHERE uuid = ?', (users, uuid,))
                    # ==============================================================================================

            c.execute('SELECT * FROM users WHERE uuid=?', (follower_uuid,))

            users = c.fetchall()[0]
            users = eval(users[4])
            users.remove(int(uuid))
            users = str(users)

            c.execute('UPDATE users SET followers = ? WHERE uuid = ?', (users, follower_uuid,))

            conn.commit()
            c.close()
            conn.close()


def is_following(uuid, follower_uuid):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))

    users = c.fetchall()[0]
    users = eval(users[3])

    if int(follower_uuid) not in users:
        return 'False'
    else:
        return 'True'


def get_follower_number(uuid):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))

    users = c.fetchall()[0]
    following = eval(users[3])
    followers = eval(users[4])

    return len(following), len(followers)


def get_followers(uuid):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))
    users = c.fetchall()[0]
    followers = eval(users[4])


    out = []

    for person in followers:
        out.append(get_info_raw_uuid(person)[0])

    return out


def is_a_follower(uuid, check_uuid):
    if uuid in get_followers(check_uuid):
        return True
    else:
        return False


def get_raw_followers(uuid):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))
    users = c.fetchall()[0]
    return eval(users[4])


def get_following(uuid):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))
    users = c.fetchall()[0]
    followers = eval(users[3])

    out = []

    for person in followers:
        out.append(get_info_raw_uuid(person)[0])

    return out


def get_following_raw(uuid):
    conn, c = __open_database()
    c.execute('SELECT * FROM users WHERE uuid=?', (uuid,))
    users = c.fetchall()[0]
    followers = eval(users[3])

    out = []

    for person in followers:
        out.append(person)

    return out


def get_all_username():
    conn, c = __open_database()
    c.execute('SELECT username, uuid, username, icon FROM users')

    out = []

    names = c.fetchall()

    for item in names:
        out.append([str(item[0]), str(item[1]), '', str(item[3]), get_rank_id(int(item[1]))])

    output(out)
    return out


def get_all_display():
    conn, c = __open_database()
    c.execute('SELECT display, uuid, username, icon FROM users')

    out = []

    names = c.fetchall()

    for item in names:
        out.append([str(item[0]), str(item[1]), str(item[2]), str(item[3])])

    return out


def get_all_uuid():
    conn, c = __open_database()
    c.execute('SELECT uuid, uuid, username, icon FROM users')

    out = []

    names = c.fetchall()

    for item in names:
        out.append([str(item[0]), str(item[1]), str(item[2]), str(item[3])])

    return out


def get_icon_ext(uuid):
    conn, c = __open_database()
    c.execute('SELECT icon FROM users WHERE uuid=?', (uuid,))
    try:
        return str(c.fetchall()[0][0])
    except IndexError:
        return False


def set_icon_ext(uuid, ext):
    conn, c = __open_database()
    c.execute('UPDATE users SET icon = ? WHERE uuid = ?', (ext, uuid,))
    conn.commit()
    c.close()
    conn.close()


def delete_user_icon(uuid):
    try:
        os.remove('{}/lookalive/static/icons/{}{}'.format(os.getcwd(), uuid, get_icon_ext(uuid)))
    except OSError:
        print ('{}/lookalive/static/icons/{}{} HAS FAILED'.format(os.getcwd(), uuid, get_icon_ext(uuid)))


def get_mutual_followers(uuid):
    conn, c = __open_database()
    mutual  = []
    followers = []
    for follower in get_followers(uuid):

        followers.append(follower[6])

    for follower in followers:
        if uuid in get_raw_followers(follower):
            mutual.append(follower)

    return mutual


def get_mutual_followers_unseen(uuid):
    conn, c = __open_database()
    mutual  = []
    followers = []
    for follower in get_followers(uuid):

        followers.append(follower[6])

    for follower in followers:
        if uuid in get_raw_followers(follower):
            mutual.append([follower,  message.get_people_unseen_messages(uuid, follower)])

    return mutual


def get_all_users_uuid():
    conn, c = __open_database()
    c.execute('SELECT * FROM users')

    all_users = c.fetchall()
    uuids = []

    for user in all_users:
        uuids.append(user[6])

    return uuids


def get_number_of_users():
    return len(get_all_users_uuid())


def get_rank_id(uuid):
    conn, c = __open_database()
    c.execute('SELECT rank FROM users WHERE uuid=?', (uuid,))
    rank = c.fetchall()[0][0]
    if rank is None:
        return 0
    else:
        return rank


def get_admin_user_display():
    conn, c = __open_database()
    c.execute('SELECT display, username, email, uuid, rank, icon, popular FROM users')
    return c.fetchall()


def set_rank_id(uuid, rank_id):
    conn, c = __open_database()
    c.execute('UPDATE users SET rank = ? WHERE uuid = ?', (rank_id, uuid,))
    conn.commit()
    c.close()
    conn.close()


def ban_user(uuid):
    set_rank_id(uuid, -1)


def pardon_user(uuid):
    set_rank_id(uuid, 0)


def get_follower_dict():
    conn, c = __open_database()

    c.execute('SELECT username FROM users')
    users = c.fetchall()

    for user in range(len(users)):
        users[user] = str(users[user][0])

    user_dict = {}

    for user in users:
        user_dict[get_user_uuid(user)] = get_follower_number(get_user_uuid(user))[1]
    return user_dict


def set_popular(uuid, state=True):
    conn, c = __open_database()
    c.execute('UPDATE users SET popular = ? WHERE uuid = ?', (int(state), uuid,))
    conn.commit()
    c.close()
    conn.close()


def get_popular(uuid):
    conn, c = __open_database()
    c.execute('SELECT popular FROM users WHERE uuid = ?', (uuid,))
    state = c.fetchall()
    conn.commit()
    c.close()
    conn.close()

    return state


def get_popular_list():
    conn, c = __open_database()
    c.execute('SELECT * FROM users')

    account = c.fetchall()

    popular = []

    for person in account:
        status = get_popular(person[6])[0][0]
        if status == 1 or get_follower_number(person[6])[1] >= int(config.popular_follower_cap()):
            popular.append( person[6] )

    return popular


def get_display_popular():
    conn, c = __open_database()
    c.execute('SELECT * FROM users')
    accounts = c.fetchall()

    popular = []

    # 0 - Display Name
    # 1 - User Name
    # 6 - UUID
    # 9 - Force Popular
    # get_follower_number(UUID)[1] - Enough Followers

    for account in accounts:
        user_temp = [account[0], account[1], account[6], account[9], get_follower_number(account[6])[1]]
        if user_temp[3] is None:
            user_temp[3] = False

        user_temp[3] = bool(user_temp[3])

        if user_temp[4] >= config.popular_follower_cap():
            user_temp[4] = True
        else:
            user_temp[4] = False

        if user_temp[3] is True or user_temp[4] is True:
            popular.append(user_temp)

    output(popular)
    return popular











