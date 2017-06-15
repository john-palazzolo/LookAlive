import sqlite3
import os

import things
import notification
import users


def __open_database():
    # This function connects to and returns the database object

    # open the database
    conn = sqlite3.connect('lookalive/databases/users.db')

    # create teh cursor object
    c = conn.cursor()

    # return the connection and cursor
    return conn, c


def add_comment(comment, uuid, image=0, flagged='True'):
    # this function adds a comment to the server

    # get a time and date stamp from the things module
    date = things.get_time()
    delete = -1 # 86400 secconds in a day multiplied by 10 days (The message lives for 10 days)

    # open the sqlite db
    conn, c = __open_database()

    # get a new comment ID
    comment_id = get_id()

    # this is a str of a list usedin the db
    ls = '[]'

    #     c.execute("INSERT INTO users (display, username, password, following, followers, email, uuid) VALUES (?, ?, ?, ?, ?, ?, ?)", (display, user, password, '[]', '[]', email, uuid))
    # insert the comment into the db
    c.execute("INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (date, comment, uuid, delete, comment_id, image, ls, flagged))

    # save and close the db connection
    conn.commit()
    c.close()
    conn.close()

    # return the new comment's ID
    return comment_id


def repost(post_id, uuid):
    conn, c = __open_database()
    c.execute("SELECT * FROM comments WHERE id=?", (post_id,))

    comment = c.fetchall()[0]

    message = "{} <sub>Originaly <a href='/profile/{}'>{}</a>'s Post</sub>".format(comment[1], comment[2], users.get_username(int(comment[2])))

    if comment[5] != 0:
        things.copy_rename('lookalive/static/files/{}{}'.format(comment[4], comment[5]),
                           'lookalive/static/files/{}{}'.format(get_id(), comment[5]))

    add_comment(message, uuid, comment[5], comment[7])
    conn.commit()
    c.close()
    conn.close()


def get_comments():
    conn, c = __open_database()
    c.execute ('SELECT users.display, comments.comment, comments.uuid, comments.date, comments.id, comments.image, comments.likes, users.icon, comments.flagged, users.popular, users.rank FROM users INNER JOIN comments ON users.uuid = comments.uuid ORDER BY date')
    comments = c.fetchall()
    return comments


def get_id():
    conn, c = __open_database()
    c.execute('SELECT * FROM comments')

    all_accounts = c.fetchall()

    uuid = []

    for item in all_accounts:
        uuid.append(item[4])

    try:
        uuid = max(uuid) + 1
    except TypeError:
        uuid = 0
    except ValueError:
        uuid = 0
    return uuid


def delete_comment(comment_id):
    conn, c = __open_database()
    c.execute("SELECT image FROM comments WHERE id=?", (comment_id,))

    data = c.fetchall()
    if str(data[0]) != 0:
        data = data[0]
        path = os.getcwd() + '/lookalive/static/files/' + str(comment_id) + str(data[0])
        try:
            os.remove(path)
        except OSError:
            pass

    c.execute("SELECT * FROM comments WHERE id=?", (comment_id,))
    word = c.fetchall()

    c.execute("DELETE FROM comments WHERE id=?", (comment_id,))
    conn.commit()
    c.close()
    conn.close()

    return word[0][1]


def get_user_comment(uuid):
    conn, c = __open_database()
    c.execute('SELECT users.display, comments.comment, comments.uuid, comments.date, comments.id, comments.image, comments.likes,  users.popular FROM users INNER JOIN comments ON users.uuid = comments.uuid WHERE comments.uuid=? ORDER BY date', (uuid,))

    posts = c.fetchall()

    return posts


def like_post(uuid, post_id):
    try:
        conn, c = __open_database()
        c.execute('SELECT * FROM comments WHERE id=?', (post_id,))

        post_object = c.fetchall()
        post_object = post_object[0]

        likes = eval(post_object[6])

        if check_like(uuid, post_id) is False:
            likes.append(uuid)
            notification.add_notification(uuid, 'You Have Liked {}\'s Post!'.format(users.get_user_name(post_object[2])), post_object[2])
            notification.add_notification(post_object[2], '{} Has Liked Your Post!'.format(users.get_user_name(uuid)), uuid)
        else:
            likes = filter(lambda a: a != uuid, likes)
            notification.add_notification(uuid, 'You No Longer Like {}\'s Post!'.format(users.get_user_name(post_object[2])), post_object[2])
            notification.add_notification(post_object[2], '{} No Longer Likes Your Post!'.format(users.get_user_name(uuid)), uuid)

        c.execute('UPDATE comments SET likes = ? WHERE id = ?', (str(likes), post_id,))

        conn.commit()
        c.close()
        conn.close()
    except IndexError:
        pass



def get_likes(post_id):
    conn, c = __open_database()
    c.execute('SELECT * FROM comments WHERE id=?', (post_id,))

    post_object = c.fetchall()
    post_object = post_object[0]

    likes = eval(post_object[6])
    return len(likes)


def check_like(uuid, post_id):
    conn, c = __open_database()
    c.execute('SELECT * FROM comments WHERE id=?', (post_id,))

    post_object = c.fetchall()
    post_object = post_object[0]

    likes = eval(post_object[6])
    if uuid in likes:
        return True
    else:
        return False


def posts_by_popular(result_cap=None):
    all_comments = list(get_comments())

    all_comments = map(list, all_comments)

    for post in range(len(all_comments)):
        all_comments[post][6] = len(eval(all_comments[post][6]))


    all_comments = things.sort_index(all_comments, 6)

    all_comments.reverse()

    if result_cap is not None:
        all_comments = all_comments[:result_cap]



    return all_comments


def get_number_of_comments():
    return len(get_comments())


def inspect_message(message, check=3):
    # check:
    # 1 = flagged words
    # 2 = banned words
    # 3 = both
    # =====================
    # returned:
    # 1 = flagged word detected
    # 2 = banned word detected

    flagged_words = None

    if check == 1 or check == 3:
        temp = open(os.getcwd() + '/lookalive/security/flagged_words.txt', 'r')
        flagged_words = temp.readlines()

        for line in range(len(flagged_words)):
            flagged_words[line] = eval(flagged_words[line])[0].lower()


    banned_words = None

    if check == 1 or check == 3:
        temp = open(os.getcwd() + '/lookalive/security/banned_words.txt', 'r')
        banned_words = temp.readlines()

        for line in range(len(banned_words)):
            banned_words[line] = eval(banned_words[line])[0].lower()


    if any(ext in message.lower() for ext in banned_words):
        return 2

    if any(ext in message.lower() for ext in flagged_words):
        return 1


def get_flagged_posts():
    conn, c = __open_database()
    c.execute('SELECT * FROM comments WHERE flagged=?', (True,))

    return c.fetchall()


def ignore_post(post_id):
    conn, c = __open_database()
    c.execute('SELECT * FROM comments WHERE id = ?', (post_id,))
    word = c.fetchall()

    c.execute('UPDATE comments SET flagged = ? WHERE id = ?', ('False', post_id,))

    conn.commit()
    c.close()
    conn.close()
    return word[0][1]


def get_flagged(post_id):
    conn, c = __open_database()
    c.execute('SELECT * FROM comments WHERE id=?', (post_id,))
    return eval(c.fetchall()[0][7])
