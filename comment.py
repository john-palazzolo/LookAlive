# import built-in modules
import sqlite3      # SQLite3: Allows for database operations
import os           # OS: Allows for operating system operations

# import custom libraries
import things       # Things: This module handles misc. operations
import notification # Notification: This module handles user notifications
import users        # Users: This module handles the users on the server


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

    # insert the comment into the db
    c.execute("INSERT INTO comments VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (date, comment, uuid, delete, comment_id, image, ls, flagged))

    # save and close the db connection
    conn.commit()
    c.close()
    conn.close()

    # return the new comment's ID
    return comment_id


def repost(post_id, uuid):
    # this function allows a user to repost someone else's, or their own, post

    # connect to the database
    conn, c = __open_database()

    # get the comment that will be reposted based off the ID (Parameter 1)
    c.execute("SELECT * FROM comments WHERE id=?", (post_id,))

    # Convert the two dimesnional array to a flat tuple of just the first item (there shoild only be one comment with
    # each ID)
    comment = c.fetchall()[0]

    # format the message to credit the original user in a subscript (HTML in posts are is rendered)
    message = "{} <sub>Originally <a href='/profile/{}'>{}</a>'s Post</sub>".format(comment[1], comment[2],
                                                                                    users.get_username(int(comment[2])))

    # check if there is a picture/image attached to the post
    if comment[5] != 0:

        # if there is, use the "things" module to copy, and rename the posts image
        things.copy_rename('lookalive/static/files/{}{}'.format(comment[4], comment[5]),
                           'lookalive/static/files/{}{}'.format(get_id(), comment[5]))

    # use this module to write the new post to the database
    add_comment(message, uuid, comment[5], comment[7])

    # save and close the database connection
    conn.commit()
    c.close()
    conn.close()


def get_comments():
    # this function retuns all of the comments in the system
    # it will join the users database and the comments database

    # connect to the database
    conn, c = __open_database()

    # join the databases together
    c.execute ('SELECT users.display, comments.comment, comments.uuid, comments.date, comments.id, comments.image, '
               'comments.likes, users.icon, comments.flagged, users.popular, users.rank FROM users INNER JOIN '
               'comments ON users.uuid = comments.uuid ORDER BY date')

    # get all of the comments
    comments = c.fetchall()

    # return the comments
    return comments


def get_id():
    # this function generates a new comment ID

    # connect to the database
    conn, c = __open_database()

    # select all of the comments
    c.execute('SELECT * FROM comments')

    # save the comments to a variable
    all_accounts = c.fetchall()

    # an empty list is created to store all of the comment IDs
    uuid = []

    # iterate through each comment in the system
    for item in all_accounts:

        # add the ID to the empty list
        uuid.append(item[4])

    # attempt to add 1 to the highest ID in memory
    try:
        # add 1
        uuid = max(uuid) + 1

    except TypeError:
        # if the highest value is nit a number, set the value to 0
        uuid = 0

    except ValueError:
        # if no values exist, set the value to 0
        uuid = 0

    # return the new comment id
    return uuid


def delete_comment(comment_id):
    # this function deletes the comment based on the provided comment ID

    # connect to the database
    conn, c = __open_database()

    # pull the comment to delete into memory, do determine if there is a file to delete too
    c.execute("SELECT image FROM comments WHERE id=?", (comment_id,))

    # save the comment into a variable
    data = c.fetchall()

    # check if there is a file associated with this file
    if str(data[0]) != 0:

        # if there is , extract the file extension
        data = data[0]

        # generate the absolute path of the file using the comment ID, and the file extension
        path = os.getcwd() + '/lookalive/static/files/' + str(comment_id) + str(data[0])

        try:
            # attempt to delete the file
            os.remove(path)

        except OSError:
            # if this fails due to the file not existing
            pass

    # pull the comment into memory again, this is so the comment can be returned
    c.execute("SELECT * FROM comments WHERE id=?", (comment_id,))

    # save to a variable
    word = c.fetchall()

    # delete the comment from the database
    c.execute("DELETE FROM comments WHERE id=?", (comment_id,))

    # save and close the database connection
    conn.commit()
    c.close()
    conn.close()

    # return the message that was deleted
    return word[0][1]


def get_user_comment(uuid):
    # this function returns the comments of a user, nased if the provided UUID

    # connect to the database
    conn, c = __open_database()

    # return all of the posts ordered by date posted
    c.execute('SELECT users.display, comments.comment, comments.uuid, comments.date, comments.id, comments.image, '
              'comments.likes,  users.popular FROM users INNER JOIN comments ON users.uuid = comments.uuid WHERE '
              'comments.uuid=? ORDER BY date', (uuid,))

    # save the posts to a variable
    posts = c.fetchall()

    # return the posts
    return posts


def like_post(uuid, post_id):
    # this function makes a user like a post

    try:
        # connect to the database
        conn, c = __open_database()

        # select the post from the database
        c.execute('SELECT * FROM comments WHERE id=?', (post_id,))

        # pull the results into memory
        post_object = c.fetchall()

        # get the post into a flat tuple
        post_object = post_object[0]

        # cast the list of users who like a post from a string of a list to an actual list
        likes = eval(post_object[6])

        # check if the user already likes the post
        if check_like(uuid, post_id) is False:
            # if they do not, add the uuid to the list of likes
            likes.append(uuid)

            # notify the person who has liked the post, and the post owner about the action
            notification.add_notification(uuid, 'You Have Liked {}\'s Post!'.format(users.get_user_name(post_object[2])), post_object[2])
            notification.add_notification(post_object[2], '{} Has Liked Your Post!'.format(users.get_user_name(uuid)), uuid)
        else:
            # if they already like the post, remove the post from the list
            likes = filter(lambda a: a != uuid, likes)

            # notify the person who has liked the post, and the post owner about the action
            notification.add_notification(uuid, 'You No Longer Like {}\'s Post!'.format(users.get_user_name(post_object[2])), post_object[2])
            notification.add_notification(post_object[2], '{} No Longer Likes Your Post!'.format(users.get_user_name(uuid)), uuid)

        # re-write the list to the database
        c.execute('UPDATE comments SET likes = ? WHERE id = ?', (str(likes), post_id,))

        # save and close the database connection
        conn.commit()
        c.close()
        conn.close()

    except IndexError:
        # if this fails (due to the requested post not existing)
        # do not do anything
        pass


def get_likes(post_id):
    # this function returns the number of likes a post has

    # connect to the database
    conn, c = __open_database()

    # select the specified post from the database
    c.execute('SELECT * FROM comments WHERE id=?', (post_id,))

    # save the post to a variable
    post_object = c.fetchall()

    # take the first post with the specified id (there should only be 1)
    post_object = post_object[0]

    # convert the post's likes from a string of a list to a list
    likes = eval(post_object[6])

    # return the total amount of likes
    return len(likes)


def check_like(uuid, post_id):
    # this function determines if a user likes a post

    # connect to the database
    conn, c = __open_database()

    # select the comment from the database
    c.execute('SELECT * FROM comments WHERE id=?', (post_id,))

    # save the comment to a variable
    post_object = c.fetchall()

    # get the first post with the specified id (THERE CAN BE ONLY ONE!)
    post_object = post_object[0]

    # convert the post's likes from a string of a list to an actual list
    likes = eval(post_object[6])

    # check if the UUID passed in as parameter 1 is in the list
    if uuid in likes:
        # if it is, return True
        return True

    else:
        # if not, return False
        return False


def posts_by_popular(result_cap=None):
    # this function returns a list of the posts ordered by popularity.
    # the optional parameter allows for a result cap (default is no cap)

    # get all of the comments in the database as a list
    all_comments = list(get_comments())

    # convert all tuples inside the outside list to a list
    all_comments = map(list, all_comments)

    # iterate through all of the posts
    for post in range(len(all_comments)):

        # convert the string of list of likes to the number of likes
        all_comments[post][6] = len(eval(all_comments[post][6]))

    # use the things module to sort the comments array according th likes (6th index)
    all_comments = things.sort_index(all_comments, 6)

    # reverse the list to make the most popular go first
    all_comments.reverse()

    # check if a parameter was passed in for the cap variable
    if result_cap is not None:

        # if a value is, cap off the results at that number
        all_comments = all_comments[:result_cap]

    # return the newly sorted array
    return all_comments


def get_number_of_comments():
    # this function returns the number of comments in the system

    # return the length of all of the comments
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
