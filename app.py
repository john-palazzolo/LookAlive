# Python Flask Imports
from flask import Flask, request, render_template, redirect, session, flash

# Built-in module imports
import random
import os
import time
import datetime



# Custom module imports
import holiday
import users
import comment
import things
import notification
import message
import uac
import preset
import config
import log

from builtin import *

# # generate a security key:
# os.urandom(24)


def all_follow_lookalive_account(user_id):
    # TODO: Optimise this function. It is exremly redundant
    # this fuction makes all users who are not the specified account
    # follow the account

    # get a list of all of the UUIDs in the database
    uuids = users.get_all_users_uuid()

    # Iterate through the UUIDs
    for uuid in uuids:
        # check if the current UUID is not equal to the UUID passed in
        # ( if the person is not the person everyone will follow
        if int(uuid) != user_id:
            # if not, force the accound to follow the specified UUID
            users.follow(uuid, user_id, False, False)

# set the 3 owner accounts to owner rank. This is a failsafe to prevent
# accidetal account corruption of an owner
users.set_rank_id(0, 4)     # Christopher P.
users.set_rank_id(1, 4)     # Nick B.
users.set_rank_id(15, 4)    # LookAlive

# all_follow_lookalive_account(some_uuid)   # NOTE: 'some_uuid' is psudo code variable name. Please change to an actual UUID if the function call is used

# Declare Flask dependent variables
app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # this one is for file upload

# get the security key from the key text file 'key.txt'
temp = open('lookalive/key.txt', 'r')
# get the first line. it is the key
data = str(temp.readlines()[0])
# Close the file
temp.close()

# Set the Session Variable secret key
app.config['SECRET_KEY'] = data

# clear the output file
clear_file()

@app.context_processor
def inject_dict_for_all_templates():
    # this contructor injects the variables, and values stored in this dict to
    # ALL HTML templates
    return dict(logo=preset.get_preset_props()['logo'], user_follower=users.get_popular_list(), popular_min_followers=config.popular_follower_cap(), popular_picture=preset.get_preset_props()['popular_picture'])

# ==============================================================================
# Front End
# ==============================================================================

@app.route('/')
def index():
    # check if the user is logged in with a valid account
    if 'user' in session:
        # If they are good, get the info about their account
        user = users.get_info(session['user'])
        # get all of the posts on the server
        posts = comment.get_comments()

        # if the user does not exist, kick them to the login page
        if user is None:
            return redirect('/login')

        # get the user's UUID
        uuid = user[6]

        # get unseen private messages
        unseen = message.get_unseen_messages(uuid)

        # check to see if 'View all comments' mode is enabled
        if config.view_all_comments() is False:
            # if it is not, remove all of hte comments the user can not see

            # generate a list of the UUIDs the user can see content from
            include = users.get_following_raw(uuid)

            # add the user's UUID to that list
            include.append(uuid)

            # now filter all of the comments the user is allowed to see
            comments = []

            # iterate through all of the users that can be viewed
            for dude in include:
                # append all of the user's comments to the comments list
                comments.append(comment.get_user_comment(dude))

            # Convert the 2 dimensional array to a 1 dimensional array (list)
            comments = sum(comments, [])

            # sort all of the comments according to the third index (tima/date stamp)
            posts = things.sort_index(comments, 3)

        # check if no posts are available to the user
        if posts is None:
            # if no posts are available, make the current posts to an ampty list
            posts = []

        # some post elements need to be reformatted. this is done here
        # iterate through all of the visible posts
        for item in range(len(posts)):
            # cast each post to a list (just in case)
            posts[item] = list(posts[item])
            # set the 6th element of the post object to the list of likes it has
            posts[item][6] = comment.get_likes(posts[item][4])
            # Add the users icon extension to the post object (.png, .jpg, etc.)
            posts[item].append(users.get_icon_ext(int(posts[item][2])))
            # Add the flagged status to the object
            posts[item].append(comment.get_flagged(int(posts[item][4])))
            # Add the rank ID to the object
            posts[item].append(users.get_rank_id(int(posts[item][2])))

        # reverse the sorted posts, to make them newest first
        posts.reverse()

        # render the home HTML page
        return render_template('index.html', posts=posts, name=user[0], uuid=user[6], ext=users.get_icon_ext(user[6]), unseen=unseen, notify=notification.get_notifications_number(user[6]))
    else:
        # if the user does not have a propper session variable, send them to the login page
        return redirect('/login')


@app.route('/eula')
def eula():
    # this page displayes the EULA. The EULA is stored in a server file

    # start by opening the file, and pulling the contents into memory
    temp = open('lookalive/legal/eula.txt')
    data = temp.readlines()
    temp.close()

    # display the EULA in the 'eula.html' template
    return render_template('eula.html', eula=data)


@app.route('/login')
def login():
    # this page allows the user to log in to, or register to the website.
    # this is just the front end. the back end operations are done elsewhere

    # get an array of all of the balloons to display. if this is disabled
    # no array will be generated. - Birthday
    balloons = get_balloon_array(50)

    # get an array of all of the snow flakes to display. if this is disabled
    # no array will be generated. - Christmas
    snow_flake = get_snow_flake_array(100)

    try:
        if int(config.motd()) == 1:

            # get the wacky holiday for today's date (+0000 UTC)
            if holiday.check() is not False:

                # if there is a holiday, use the custom HTML flash engine to display the holiday
                flash(["Today Is {}".format(holiday.check()), config.motd_mode()])
        else:
            flash([config.motd(), config.motd_mode()])
    except ValueError:
        flash([config.motd(), config.motd_mode()])

    # serve the HTML file, with the balloons array, and snowflake array.
    return render_template('login.html', balloons=balloons, snow_flake=snow_flake)


@app.route('/register', methods=['POST'])
def login_register():
    # this page attempts to create an account for the user, based on the registration form
    # on the login (/login) page

    # get all of the user inputs from the reginstration page, and save the values
    # into respective variables
    display = request.form['display']
    user = request.form['user']
    pass_1 = request.form['pass_1']
    pass_2 = request.form['pass_2']
    email = request.form['email']

    # check if the user name is in use
    if users.username_verify(user) is False:

        # if the username is used, serve the 'login.html' file, with an error message
        return render_template('login.html', error="Username Is In Use")

    # check if the password, and password verification match
    if pass_1 == pass_2:
        # if they do, go ahead and create the account
        users.new_user(display, user, pass_1, email)
    else:
        # if hte passwords do not match, serve the 'login.html' file with an error message
        return render_template('login.html', error="Passwords Do Not Match")

    # if the code has run this far, the account is valid, and has been sucsessfully created
    # write the account to the user's session variable
    session['user'] = user

    # redirect the user to the home page
    return redirect('/')


@app.route('/log_in', methods=['POST'])
def login_login():
    # this page handles a login request based on the login form on the login (/login) page

    # get all of the user inputs from the login page, and save the values
    # into respective variables
    user = request.form['user']
    password = request.form['password']

    # with the users module, determine if the requested account exists
    if users.login(user, password) is True:

        # if the account exists, write the account to the user's session variable
        session['user'] = user

        # redirect the user to the home page
        return redirect('/')

    else:
        # if the account does not exits, serve the 'login.html' file with an error message.
        return render_template('login.html', error_2="Account Does Not Exist!")


@app.route('/post', methods=['POST'])
def post():
    # this page handles posting a post on the home page on the website

    # check if the user is logged into a valid account (check session variable)
    if 'user' in session:

        # get the user's data object
        user = users.get_info(session['user'])

        # get the user's rank
        rank = users.get_rank_id(user[6])

        # check if the user is banned (rank=-1)
        if str(rank) == str(-1):

            # if the user is banned, use the UAC module to generate a banned
            # message to the user
            flash([uac.get_banned_message('You Can Not Post Anything'), 0])
            return redirect(request.referrer)

        # if the user is not banned, allow them to post

        # get the message from the form
        msg = request.form['message']

        # check if the message is just the default text
        if msg == "Write Something Here":

            # if it is, set the post message to an empty string
            msg = ""

        # inspect the message for banned, or flagged words
        check = comment.inspect_message(msg)

        # set the message flagged status to 0
        flagged = 0

        # determine if a bad word has been detected
        if check is not None:

            # check if a flagged word is detected
            if check == 1:

                # if it is, use the custom flash engine to alert the user. use "Warning" (1) mode.
                flash(['A Flagged Word Has Been Detected In Your Post. The Post Will Be Posted, And Evaluated By A Moderator.', 1])

                # set the status to 1 (flagged word detected)
                flagged = 1

            # check if a banned word has been detected
            if check == 2:
                # if it is, use the custom flash engine to alert the user. use "Bad" (0) mode.
                flash(['A Banned Word Has Been Detected In Your Post. The Post Will Not Be Posted.', 0])

                # redirect the user to the home page. do not write the message to the server
                return redirect('/')

        # if the message is OK to post, continue execution

        # get the user's UUID
        uuid = users.get_user_uuid(session['user'])

        # get a list of the uploaded files
        file = request.files.getlist("fileSelect")

        # create a variable which will help determine if any files are uploaded
        do_file = True

        try:
            # attempt to save the first file in the list of files
            file = file[0]

        except IndexError:
            # if there is no file, do not allow file upload
            do_file = False

        # determine if the file is present from the previous check
        if do_file is True:
            # if a file is present, do this nonscence.

            # generate the path to save the file
            target = os.path.join(APP_ROOT, os.getcwd() + '/lookalive/static/files')

            # grab the raw name of the file
            filename = file.filename

            try:
                # attempt the following

                # get the location of the '.' character. (seproates the name and extension)
                location = filename.index('.')

                # write the message to the server, using the file extension as the image refrence
                file_name = comment.add_comment(msg, uuid, filename[location:], flagged)

                # generate the file name with the file extension
                filename = str(file_name) + filename[location:]

                # combine the server file path, and name of the file
                destination = "/".join([target, filename])

                # save the file to the above location
                file.save(destination)

            except ValueError:
                # if the '.' character is not in the filename (No file extension)
                # the file will not be allowed to be uploaded to the server.

                # write the message to the server without the file attachment
                file_name = comment.add_comment(msg, uuid, flagged=flagged)
        else:
            # if no file is attempted to be uploaded, write hte messgae to the server
            # do not include a file attachment
            file_name = comment.add_comment(msg, uuid, flagged=flagged)

        # redirect the user to the home page
        return redirect('/')
    else:
        # if the user is not logged into a valid account, kick them to the login page
        return redirect('/login')


@app.route('/post/delete/<uuid>/<post>/<redir>')
def post_delete(uuid, post, redir):
    # this function will delete a post, and attached files from the server

    # set a default value for 'location' variable. this will be the spot
    # the user will be redirected when a post is deleted, based off the ID
    # in the 'redir' parameter
    location = '/'

    # check the redirection location
    if str(redir) == '0':

        # if the ID is 0, redirection location is the home page
        location = '/'

    elif str(redir) == '1':
        # if the ID is 1, redirection location is the user page
        location = '/profile/{}'.format(uuid)

    # get the user's UUID from the session variable
    use_uuid = users.get_user_uuid(session['user'])

    # check if the uuid of the logged-in user is the same UUID as the post owner
    if int(uuid) == int(use_uuid):
        # if they match, use the 'comment' module to delete the post
        comment.delete_comment(post)

        # redirect the user to the previously determined location
        return redirect(location)

    else:
        # if the UUIDs do not match, redirect the user to the previously determined location
        return redirect(location)


@app.route('/post/like/<post>')
def like_post(post):
    # this page makes a user like a post

    # use the comment module to make the logged in user like the post
    # the post is specified by ID from the paramaters
    comment.like_post(users.get_user_uuid(session['user']), post)

    # make the user go back to the previously viewed page
    return redirect(request.referrer)


@app.route('/repost/<post>')
def repost(post):
    # get the user's data object
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user is banned (rank=-1)
    if str(rank) == str(-1):

        # if the user is banned, use the UAC module to generate a banned
        # message to the user
        flash([uac.get_banned_message('You Can Not Post Anything'), 0])
        return redirect(request.referrer)

    comment.repost(int(post), int(user[6]))
    return redirect(request.referrer)


@app.route('/profile/<uuid>')
def profile_default(uuid):
    # this page is a redirection page. this was the old way of viewing a profile
    # it no longer works, but most links to go to a profile page point here.
    # this is left as it is easier that going through all of the HTML files.

    # redirect the user to the propper profile page, with view ID 0 (Posts)
    return redirect('/profile/{}/0'.format(uuid))


@app.route('/profile/<uuid>/<view>')
def profile(uuid, view):
    # this page handles the viewing of profile pages

    # check if the user is logged in
    if 'user' in session:
        # if hte user is logged in, continue execution.

        # get the name of hte page owner
        page_owner = users.get_user_name(uuid)

        # get the information of the page owner
        page_owner_info = users.get_info(page_owner)

        # get information about the user
        user = users.get_info(session['user'])

        # rename the UUID of hte page
        page_uuid = uuid

        # check to see if the page owner is following the user from the 'users' module
        follow_back = users.is_following(uuid, user[6])

        # check to see if the user is following the page owner from the 'users' module
        following = users.is_following(user[6], page_uuid)

        # get all of the comments of the page owner
        posts = comment.get_user_comment(uuid)

        # reverse the list to make the newest posts first
        posts.reverse()

        # get the ammount of accounts that follow the page ower from the 'users' module
        follow_number = users.get_follower_number(page_uuid)

        # get the page owner's icon file extension
        img_ext = users.get_icon_ext(page_uuid)

        rank = users.get_rank_id(page_uuid)
        # check if the page owner has any posts
        if posts is None:
            # if they do not, set the list of posts to an empty list
            posts = []

        # check the view mode, and serve the propper HTML file
        if view == '0':
            # if the mode is 0, serve "post" mode
            return render_template('profile.html', name=user[0], uuid=user[6], page_name=page_owner_info[0], username=page_owner_info[1], posts=posts, page_uuid=page_uuid, following=following, follow_number=follow_number, img_ext=img_ext, ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), follow_back=follow_back, rank=rank)

        elif view == '1':
            # if the mode is 1, serve "image" mode
            return render_template('profile_image.html', name=user[0], uuid=user[6], page_name=page_owner_info[0], username=page_owner_info[1], posts=posts, page_uuid=page_uuid, following=following, follow_number=follow_number, img_ext=img_ext, ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), follow_back=follow_back, rank=rank)

        elif view == '2':
            # if the mode is 2, serve "edit" mode

            # check if the user is logged in as the page owner
            if str(user[6]) == str(uuid):
                # if the user is, serve the profile edit form
                return render_template('profile_edit.html', name=user[0], uuid=user[6], page_name=page_owner_info[0], username=page_owner_info[1], posts=posts, page_uuid=page_uuid, img_ext=img_ext, ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), rank=rank)
            else:
                # if the user is not, redirect the user back to "image" mode
                return redirect('/profile/{}/0'.format(uuid))

        elif view == '3':
            # if the mode is 3, serve "private messager" mode
            return redirect('/message/{}'.format(page_uuid))

        elif view == '4':
            # if the mode is 4, make the logged in user, follow the page owner
            users.follow(user[6], uuid)

            # redirect the user back to "post" mode
            return redirect('/profile/{}/0'.format(uuid))

        elif view == '5':
            # if the mode is 5, serve "page owner followers" mode

            # get the list of users who follow the page owner
            people = users.get_followers(page_uuid)
            return render_template('profile_followers.html', name=user[0], uuid=user[6], page_name=page_owner_info[0], username=page_owner_info[1], posts=posts, page_uuid=page_uuid, followers=people, action="Followers", ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), rank=rank)

        elif view == '6':
            # if the mode is 6, serve "page owner following" mode

            # get a list of users who the page owner follows
            people = users.get_following(page_uuid)
            return render_template('profile_followers.html', name=user[0], uuid=user[6], page_name=page_owner_info[0], username=page_owner_info[1], posts=posts, page_uuid=page_uuid, followers=people, action="Following", ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), rank=rank)

        else:
            # if no mode is recognized, redirect the user to "text" mode
            return redirect('/profile/{}/0'.format(uuid))
    else:
        # if the user is not logged in, rediret them to "post" mode
        return redirect('/login')


@app.route('/profile_edit/<uuid>', methods=['POST'])
def edit_profile(uuid):
    # this page handles the editing of profiles on the server

    # create 2 variables to check if a failure has occoured, and a message
    fail = False        # fail status
    error = "none"      # error message

    # Get All values from the edit form
    display = request.form['display']               # dislay name
    username = request.form['user']                 # username
    email = request.form['email']                   # E-Mail Address
    password = request.form['password']             # password
    old_password = users.get_password(int(uuid))
    file = request.files.getlist("icon")            # icon upload

    # check if there is a file uploaded for the icon
    if file[0].filename != '':
        # if one is uploaded...

        # get the file extension of the image with the 'things' module
        ext = things.extensionify(file[0].filename)[1]

        # delete the user's current icon (user's module)
        users.delete_user_icon(uuid)

        # set the new icon to the user's account (user's module)
        users.set_icon_ext(uuid, ext)

    # get the name of the page owner
    page_owner = users.get_user_name(uuid)

    # get other information about the page owner
    page_owner_info = users.get_info(page_owner)

    # get information about the logged in user
    user = users.get_info(session['user'])

    # rename the page UUID variable
    page_uuid = uuid

    # using the built-in hash algorithm, check if the 'old password' matches the
    # user's password
    if str(users.hash_password(old_password)) != str(user[2]):
        # if they do not match, update the fail variables to True, and a message
        pass

    # attempt to update the user. if the function returns 'False' it means the
    # requested username is in use.
    if users.update_user(display, username, email, password, old_password, session['user']) is False:
        # if it is in use, update the fail variables to True, and a message
        fail = True
        error = "Username In Use!"

    else:
        # if the account update has sucseeded, continue execution

        # crate a variable to store an icon update action
        do_file = True
        try:
            # attempt to grab the first uploaded file
            file = file[0]

        except IndexError:
            # if this fails, do not update user icon
            do_file = False

        # check if the file is ok to update
        if do_file is True:
            # if it is, generate the path to save the file
            target = os.path.join(APP_ROOT, os.getcwd() + '/lookalive/static/icons')

            # get the name of the file
            filename = file.filename

            try:
                # attempt to locate the index of the '.' character. This breaks
                # the file name from the extension
                location = filename.index('.')

                # Generate a file name from the name of the file, and the extension
                filename = str(page_uuid) + filename[location:]

                # concatanate the location of the save path and the file name
                destination = "/".join([target, filename])

                # save the file to the destanation
                file.save(destination)

            except ValueError:
                # if no file was uploaded in the form, take no action
                pass

    # check if an error has occoured
    if fail is True:

        # if one has, alert the user of the error, using the custom flash engine
        # using a level 0 (Bad) box
        flash(["Error: {}!".format(error), 0])

        # redirect the user to "post" mode
        return redirect('/profile/{}/0'.format(uuid))

    else:
        # if there was no faiures, and the user name was updated,
        if username != '':
            # update the session variable with the new user name
            session['user'] = username

        # alert the user the account was updated sucsessfuly, using the custom
        # flash engine, with the default level 2 (Good)
        flash("The Account Has Been Sucsessfuly Updated!")

        # redirect the user to "post" mode
        return redirect('/profile/{}/0'.format(uuid))


@app.route('/logout')
def log_out():
    # This page executes the log out procedure

    # clear the session variable
    session.clear()

    # redirect the user to the log in page
    return redirect('/login')


@app.route('/search')
def search():
    # this page displays the empty search form

    # get information about the user from the session variable
    user = users.get_info(session['user'])

    # render the HTML template
    return render_template('search.html', name=user[0], uuid=user[6], ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]))


@app.route('/search/request', methods=['POST'])
def search_request():
    # this page executes a search request by displaying the results
    # showing the most relevant items first.

    # get information about hte logged in user
    user = users.get_info(session['user'])

    # get the search query, from the text box with ID 'query'
    query = request.form['query']

    # get the number of results to display from the dropdown 'selectbasic'
    results = request.form['selectbasic']

    # this variable changes based on the search status code
    code = 0

    # check if the search query is "Galaxy Wide Domination" (An Easter Egg)
    if str(query) == "Galaxy Wide Domination":
        # if it is, set the status code to 1
        code = 1

    # get a list of all of hte users who could be selected
    possible = users.get_all_username()

    # check if the amount of results display ID is -1
    if int(results) == -1:
        # if it is, match the searh query with each user to order them accordingly
        # do not limit the amount of results (show all of them)
        order = things.match_list(str(query), possible)

    else:
        # if the amount of results is anything but -1,
        # match the searh query with each user to order them accordingly
        # limit the results to the amount the user specifies in the dropdownn
        order = things.match_list(str(query), possible)[:int(results)]

    # render the template with the results
    return render_template('search.html', name=user[0], uuid=user[6], results=order, query=str(query), ext=users.get_icon_ext(user[6]), code=code, unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]))


@app.route('/notifications/<uuid>')
def notification_page(uuid):
    # this page displays the notifications accordig to 'UUID'

    # get the data about the logged in user
    user = users.get_info(session['user'])

    # if the UUIDs do not match, log the user out
    if str(user[6]) != str(uuid):
        return redirect('/logout')

    # render the template with the user's notifications
    return render_template('notification.html', name=user[0], uuid=user[6], notification=notification.get_notifications(uuid), ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]))


@app.route('/notifications/<uuid>/delete/<note_id>')
def notification_page_delete_id(uuid, note_id):
    # this page takes care of deleting a notification

    # delete the notification with the matching ID.
    # if the specified ID is 'all', every notification is deleted
    notification.delete_notification(uuid, note_id)

    # redirect the user back to their notirications page
    return redirect('/notifications/{}'.format(uuid))


@app.route('/message')
def message_menu():
    # this page allows the user to choose an other user who are mutual followers
    # and privatly message them

    # get information about hte user
    user = users.get_info(session['user'])

    # get a list of the the mutual followers the logged in user has
    mutual = users.get_mutual_followers(user[6])

    # iterate through each mutual follower UUIDs
    for item in range(len(mutual)):
        # for each uuid in the mutual followers list,
        # set to the mutual follower's raw data, the number of the logged in user's un seen messages with the mutual follower, and the
        # mutual follower's UUID
        mutual[item] = [users.get_info_raw_uuid(mutual[item]), message.get_people_unseen_messages(int(user[6]), int(mutual[item]))]

    # render the template
    return render_template('message_menu.html', name=user[0], uuid=user[6], mutual=mutual, ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]))


@app.route('/message/<recipiant>')
def message_person(recipiant):
    # this page allows a user to provatly message a UUID

    # get the info about the logged in user
    user = users.get_info(session['user'])

    # get the user to see all of the messages between the logged in user, and the user they are following
    message.see_messages(int(user[6]), int(recipiant))

    # this variable is created to store any error messages that may occur
    error_message = None

    # this code ensures a user can only message a mutual follower, who is not themself

    # check if the attempted recipiant is not a mutual follower
    if int(recipiant) not in users.get_mutual_followers(user[6]):
        # if they are not mutual followers, create a variable to popuate the error_message variable
        error_message = 'You Can Only Message People You Follow, And People Who Follow You!'

    # check if hte indended recipiant is the logged in user
    if int(recipiant) == int(user[6]):
        # if the indended recipiant is the logged in user, popuate the error_message variable
        error_message = 'You Can Not Message Yourself You Narcissist!'

    try:
        # attempt to get the username of the recipiant
        recipiant_username = users.get_username(int(recipiant))
    except IndexError:
        # if this fails, the recipaint account does not exits, so popuate the error_message variable
        error_message = 'The Account You Have Requested Does Not Exist!'
        recipiant_username = recipiant

    # check if there is an error message
    if error_message is not None:
        # if there is, render the HTML template, of the menu
        # the only difference is that a JS alert box will be generated with the error
        # message stored inside the error_message variable
        return render_template('message_error.html', name=user[0], uuid=user[6], error=error_message, ext=users.get_icon_ext(user[6]), recipiant=recipiant_username, unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]))

    # now that the recipiant is valid, the user will be able to message them

    # get all the private messages between the logged in user, and the recipiant
    messages = message.get_messages(user[6], recipiant)

    # reverse the messages to make the newest message at the top of the page
    messages.reverse()

    # get the username, and icon exentsion of hte logged in user, adn teh reciptiant
    recip_data = [users.get_username(recipiant), users.get_icon_ext(recipiant)]
    sender_data = [session['user'], users.get_icon_ext(user[6])]

    # render the HTML template
    return render_template('message.html', name=user[0], uuid=user[6], recipiant=recipiant, ext=users.get_icon_ext(user[6]), messages=messages, recip_data=recip_data, sender_data=sender_data, unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]))


@app.route('/message/<recipiant>/send', methods=['POST'])
def message_person_send(recipiant):
    # this page handles the sending of a private message

    # get information on the logged in user
    user = users.get_info(session['user'])

    # get the message from the HTML form
    msg = request.form['message']

    # check if hte message box contains hte default text
    if msg == "Write Something Here":
        # if it does, just set the message to nothing
        msg = ""

    # send the private message
    message.send_message(recipiant, str(user[6]), msg)

    # redirect the user back to the private messge page
    return redirect('/message/{}'.format(recipiant))


@app.route('/message/<recipiant>/delete/<msg_id>')
def message_person_delete(recipiant, msg_id):
    # this page hanldes the deletion of a message

    # TODO: make this system more secure

    # delete the message
    message.delete_message(msg_id)

     # redirect the user back to the private messge page
    return redirect('/message/{}'.format(recipiant))

@app.route('/team')
def team_page():
    # this is the team page. it displays all of hte information about each team member

    # get information about the logged in user
    user = users.get_info(session['user'])

    # get a list of team files in existance
    team_files = os.listdir(os.getcwd() + '/lookalive/team')

    # this list will store all of the real team members
    team = []

    # iterate through all of the files found
    for file in team_files:
        # check if the file starts with an underscore
        if file.startswith('_') is False:
            # if it does not, it is a valid team file

            # open the file, and add the file contents to the team array
            temp = open(os.getcwd() + '/lookalive/team/' + file, 'r')
            team.append(temp.readlines())

    # reverse the team array (so Nick's name is first)
    team.reverse()

    # iterate through each team member
    for member in team:

        # replace the 4th (0 based = 3) with the icon file extensoin
        member[3] = users.get_icon_ext(str(member[1]).rstrip('\n'))

    # this file is for the dev testers
    # open the dev tester text file
    temp = open(os.getcwd() + '/lookalive/team/_dev.txt', 'r')

    # pull the contents into memory
    dev = temp.readlines()

    # close the file
    temp.close()

    # iterat through each tester
    for tester in range(len(dev)):

        # remove all of hte EOL characters in the file
        dev[tester] = eval(dev[tester].rstrip('\n'))

    # serve the HTML file
    return render_template('team.html', name=user[0], uuid=user[6], team=team, ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), dev=dev)


@app.route('/help')
def help_page():
    # this is the help page

    # get info on the logged in user
    user = users.get_info(session['user'])

    # open the FAQ text file, and pull the contents into memory
    faq = open(os.getcwd() + '/lookalive/help/faq.txt', 'r')
    faq = faq.readlines()

    # open the contct info text file, and pull the contents into memory
    contact_info = open(os.getcwd() + '/lookalive/help/contact.txt', 'r')
    contact_info = contact_info.readlines()

    # remove all of hte EOL characters in the contact info text file
    for line in range(len(contact_info)):
        contact_info[line] = contact_info[line].rstrip('\n')

    # serve the HTML file
    return render_template('help.html', name=user[0], uuid=user[6], faq=faq, ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), contact_info=contact_info)


@app.route('/help/view-all')
def help_view_all():
    # this page displays the raw qustions

    # open the file, and pull the contents into memory
    file_data = open(os.getcwd() + '/lookalive/help/question.txt', 'r').readlines()

    # reverse the file to make the newst questions first
    file_data.reverse()

    # serve the HTML file
    return render_template('display_list.html', display_list=file_data)


@app.route('/help/ask', methods=['POST'])
def help_page_ask():
    # this page lets the user ask a question

    # get the form inputs from the previous HTML file
    name = request.form['name']
    question = request.form['question']
    contact = request.form['contact']

    # open the old HTML file, and pull the contents into memory
    old_file = open(os.getcwd() + '/lookalive/help/question.txt', 'r')
    old_file = old_file.readlines()

    # get an ID for this question. (it is the length of the current file - 0 based)
    ask_id = len(old_file)

    # add the ID, sender, question, contact, and time stamp to the question array
    old_file.append('[{}, "{}", "{}", "{}", {}]'.format(ask_id, name, question, contact, time.time()))

    # open the file again in read mode (this clears the file)
    new_file = open(os.getcwd() + '/lookalive/help/question.txt', 'w')

    # iterate through the old file removing the remaining EOLs, and
    # adding a new one to the line. also write the line to the file
    for line in old_file:
        new_file.write(line.rstrip('\n') + "\n")

    # save and close the new file
    new_file.close()

    # TODO REDUNDNANT COIDE:
    faq = open(os.getcwd() + '/lookalive/help/faq.txt', 'r')
    faq = faq.readlines()

    # use the flash engine to inform the user the requst was sucsessful
    flash("Message Sucsessfuly Uploaded!")

    # redrect the user to the help page
    return redirect('/help')


@app.route('/popular')
def popular_posts():
    # this page allows the user to view the most popular posts

    # get information about the user (makes sure they are logged in)
    user = users.get_info(session['user'])

    # get the maximum number of posts (set in admin ctrl pannel)
    cap = config.number_of_popular_posts()

    # get a list of the most popular posts
    comments = comment.posts_by_popular(cap)

    # serve the HTML file
    return render_template('popular.html', comments=comments, name=user[0], uuid=user[6], ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), cap=cap)

# ==============================================================================
# Control Pannel
# ==============================================================================

@app.route('/admin')
def admin():
    # this is the home page of the control pannel

    # get information about the user
    user = users.get_info(session['user'])

    # get the rank of the user
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 1: # Jr Mod +
        # if they can not, send them to the previously viewed page
        return redirect(request.referrer)

    # get website statistics to show

    # get the number of users
    number = users.get_number_of_users()

    # get the number of website posts
    comments = comment.get_number_of_comments()

    # get the number of private messages
    private_messages = message.get_number_private_messages()

    # serve the HTML file
    return render_template('admin_home.html', number=number, comments=comments, private_messages=private_messages)


@app.route('/admin/users')
def admin_users():
    # this page displays a table of all of the users inb the system
    # profile information can be updated through here

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 1: # Jr. Mod+
        # if they can not, redirect the to the previously viewed page
        return redirect(request.referrer)

    # get an array of the information to display about each user
    user_info = users.get_admin_user_display()

    # serve the HTML file
    return render_template('admin_users.html', users=user_info, index=0, rev=True)


@app.route('/admin/users/view/<view>')
def admin_users_view(view):
    # this page allows the user to view the users
    # in a sorted manner, based on the parameter 'view'

    # ids:
    # 0: Display Name
    # 1: User Name
    # 2: Email
    # 3: UUID
    # 4: Rank

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this pahe
    if rank < 1: # Jr. Mod+
        # if they can not, redirect them to the previously viewed page
        return redirect(request.referrer)

    # get an array of the users in the system
    user_info = users.get_admin_user_display()

    # serve the HTML file
    return render_template('admin_users.html', users=user_info, index=str(view), rev=True)


@app.route('/admin/users/view/<view>/<state>')
def admin_users_view_state(view, state):
    # this page allows the user to view the users
    # in a sorted manner, with ascending/decending order,
    # based on the parameter 'state'

    # state ID:
    # a: ascending
    # d: decending

    # view ID:
    # 0: Display Name
    # 1: User Name
    # 2: Email
    # 3: UUID
    # 4: Rank

    # get basic info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this page
    if rank < 1: # Jr. Mod+
        # if they can not, return them to the prevoiusly viewed page
        return redirect(request.referrer)

    # get an array of the users in the system
    user_info = users.get_admin_user_display()

    # by defult decending order is userd
    rev=True

    # check if the state ID is 'a'
    if str(state) == 'a':
        # if it is, use ascending order
        rev=False

    # check if the state ID is 'd'
    elif str(state) == 'd':
        # if it is, use decending order
        rev=True

    # serve the HTML file
    return render_template('admin_users.html', users=user_info, index=str(view), state=str(state), rev=rev)


@app.route('/admin/users/<uuid>')
def admin_users_user(uuid):
    # this page allows the user to view a specific user, and make profile
    # edits

    # get info on the logged in user
    account_user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(account_user[6])

    # check if the user can access this page
    if rank < 2: # Mods+
        # if they can not, return them to the prevoiusly viewed page
        return redirect(request.referrer)

    # get current info about the user in the page
    info = users.get_info_uuid(uuid)

    # serve the HTML file
    return render_template('admin_users_user.html', user=info)


@app.route('/admin/users/<uuid>/toggle')
def admin_users_toggle_popular(uuid):
    # this page toggles if a user will be forced to be popular (the image above the profile picture)

    # get the uuid of the person who will be toggled as an integer
    uuid = int(uuid)

    # get information about the user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # ckeck if the user can access this page
    if rank < 4 : # owner+
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Owner", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get the user's current popular state
    state = users.get_popular(uuid)[0][0]

    # if the state is 'None', assume False (accounts created before the database update)
    if state is None:
        state = False

    # toggle the state
    state = not state

    # update teh account
    users.set_popular(uuid, state)

    # return them to the prevoiusly viewed page
    return redirect(request.referrer)


@app.route('/admin/users/<uuid>/go', methods=['POST'])
def admin_users_user_update(uuid):
    # this page allows a user's account to be updated

    # get information about the user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this page
    if rank < 3: # admin+
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get values from the HTML form
    display = request.form['display']           # Display Name
    username = request.form['usern']            # user name
    email = request.form['email']               # email address
    password = request.form['passw']            # password
    old_password = password
    file = request.files.getlist("profile")     # profile picture upload

    # determine if a file is being uploaded
    if file[0].filename != '':
        # if if a file is uploaded, get the file extension
        ext = things.extensionify(file[0].filename)[1]

        # delete the current image
        users.delete_user_icon(uuid)

        # save the new image to the database (not yet saving the pic)
        users.set_icon_ext(uuid, ext)

    # here is where stuff may fail
    # set this variable to 'False'. It becomes 'True' on a failure
    fail = False

    # attempt to update teh user
    if users.update_user(display, username, email, password, old_password, users.get_username(uuid, 1)) is False:
        # if the function returns 'False', the username is in use
        # set the variables to alert the useer
        fail = True
        error = "Username In Use!"

    else:
        # Set User's Icon
        do_file = True

        try:
            # check if a file is being uploaded
            file = file[0]

        except IndexError:
            # if this fails do not upload a file
            do_file = False

        # check if a file is ti be uploaded
        if do_file is True:

            # get the file target
            target = os.path.join(APP_ROOT, os.getcwd() + '/lookalive/static/icons')

            # get teh filena,e
            filename = file.filename

            try:
                # find the index of the '.' (where the name becomes teh etension)
                location = filename.index('.')

                # create the new filename with the UUID and file ext
                filename = str(uuid) + filename[location:]

                # geterate the destination
                destination = "/".join([target, filename])

                # save the file to the desination
                file.save(destination)

                # get teh file extension
                ext = filename[filename.index('.'):]

                # update the extension to teh database
                users.set_icon_ext(uuid, ext)

            except ValueError:
                # if no file is found, ignore the error
                pass

    if fail is True:
        # if an error occours, display the error, and redirect the user to
        # the prevoiulsy viewed page
        flash([error, 0])
        return redirect(request.referrer)

    # chekc if the user is able to make rank updayes
    if rank < 4: # owner+
        # if they can not, return them to the prevoiusly viewed page
        return redirect(request.referrer)

    # get the nrw rank ID from the HTML form
    new_rank = request.form['selectbasic']

    # if no value is provided for this, redirect the user back to the profile edit page
    if str(new_rank) == "None":
        return redirect('/admin/users/{}'.format(uuid))

    # set the user's rank to what is provided in the HTML form
    users.set_rank_id(uuid, int(new_rank))

    # alert teh user of the sucsess
    flash("The User Has Been Sucsessfuly Updated!")

    # write that an update has occoured to the log
    log.write_log(user[6], "Updated {} ({}) Account".format(users.get_username(uuid, 1), uuid))

    # redireect the user to the profile edit page
    return redirect('/admin/users/{}'.format(uuid))


@app.route('/admin/users/ban/<uuid>/<time>')
def admin_users_ban(uuid, time):
    # this page bans a user forom the server

    # get info about the logged in user
    user = users.get_info(session['user'])

    # get teh user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this feature
    if rank < 3: # admin+
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # ban the user
    users.ban_user(uuid)

    # write to teh log
    log.write_log(user[6], "Banned {} ({})".format(users.get_username(uuid, 1), uuid))

    # redirect the user to the profile edit page
    return redirect('/admin/users/{}'.format(uuid))


@app.route('/admin/users/pardon/<uuid>')
def admin_users_pardon(uuid):
    # this page allows a user to be unbanned (pardoned)

    # get basic informatio about the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the usser can access this page
    if rank < 3: # admin+
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # pardon the user
    users.pardon_user(uuid)

    # write to teh log
    log.write_log(user[6], "Pardoned {} ({})".format(users.get_username(uuid, 1), uuid))

    # return the user to the profile edit page
    return redirect('/admin/users/{}'.format(uuid))


@app.route('/admin/words/flagged')
def admin_words_flagged():
    # this page displays all of the words that will flag the messgae in a table

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 1: # Jr Mod +
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the text file with teh flagged words in it
    temp = open(os.getcwd() + '/lookalive/security/flagged_words.txt', 'r')

    # pull the contents into memory
    flagged_words = temp.readlines()

    # format the contents of the file
    for word in range(len(flagged_words)):

        # convert the line to a list object
        flagged_words[word] = eval(flagged_words[word])

        # add the word ID to the list object
        flagged_words[word].append(flagged_words[word][0])

        # add the actual word to the list. replace all letters in the word with astrexes ' * '
        # except for the first letter
        flagged_words[word][0] = flagged_words[word][0][0] + '*' * (len(flagged_words[word][0]) - 1)

        # serve the HTML fiel
    return render_template('admin_words_flagged.html', words=flagged_words, rank=int(rank), mode='flagged')


@app.route('/admin/words/flagged/add', methods=['post'])
def admin_words_flagged_add():
    # this page allows the user to add a flagged word to the list

    # get info on tthe logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this page
    if rank < 3: # admin +
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get the word from the HTML form. use title case for the string
    word = str(request.form['word']).title()

    # open the file with flagged words
    temp = open(os.getcwd() + '/lookalive/security/flagged_words.txt', 'r')

    # pull the file contents into memory
    devs = temp.readlines()

    # close the file
    temp.close()

    # iterarte through each word in the file
    for dev in range(len(devs)):
        # remove all of the EOL characters
        devs[dev] = eval(devs[dev].strip('\n'))

    # add the word to the file, with an ID of the word
    devs.append([word, len(devs)])

    # sort the word array based off the 1st index (the words)
    dev_array = things.sort_index(devs, 1)

    # open the file with the flagged words in write mode
    dev_file = open(os.getcwd() + '/lookalive/security/flagged_words.txt', 'w')

    # itterate through the array of words
    for dev in dev_array:

        # write each word to the file removing the EOL characters
        dev_file.write(str(dev) + '\n')

    # save and close the file
    dev_file.close()

    # write the action to the log
    log.write_log(user[6], "Added '{}' To The Flagged Words".format(word))

    # redirect the user back to the page that displays the list of flagged words
    return redirect('/admin/words/flagged')


@app.route('/admin/words/flagged/delete/<word_id>')
def admin_words_flagged_delete(word_id):
    # this page handles the deletion of a flagged word

    # get information about the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this page
    if rank < 3: # Admin+
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the text file with the flagged words
    temp = open(os.getcwd() + '/lookalive/security/flagged_words.txt', 'r')

    # pull the contents into memory
    devs = temp.readlines()

    # close the file
    temp.close()

    # declare a variable to store the index of the word to be deleted
    del_index = None

    # iterate through the list of words in the file
    for dev in range(len(devs)):

        # format each line into the propper list object, and remove the EOL characters
        devs[dev] = eval(devs[dev].strip('\n'))

        # check if the word ID is the same as the word ID of the word to be deleted
        if int(devs[dev][1]) == int(word_id):

            # if it is, set the deletion index to this line
            del_index = dev

    # get the word that will be deleted
    word = devs[del_index]

    # delete the word from the array
    del devs[del_index]

    # sort the updated array based on the 1st index (the word)
    dev_array = things.sort_index(devs, 1)

    # open the file of flagged words in write mode
    dev_file = open(os.getcwd() + '/lookalive/security/flagged_words.txt', 'w')

    # iterate through each line in the updated file
    for dev in dev_array:

        # write each line back to the text file
        dev_file.write(str(dev) + '\n')

    # save and close te file
    dev_file.close()

    # write to the log
    log.write_log(user[6], "Deleted '{}' From The Flagged Words".format(word[0]))

    # redirect the user back to the list of flagged words
    return redirect('/admin/words/flagged')


@app.route('/admin/words/banned')
def admin_words_banned():
    # this page allows the user to view the words that are not allowed to be posted AT ALL

    # get info on the loffed in user
    user = users.get_info(session['user'])

    # get hte user's rnak
    rank = users.get_rank_id(user[6])

    # check if the user can access this paghe
    if rank < 1: # Jr Mod +
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the file containing the banned words
    temp = open(os.getcwd() + '/lookalive/security/banned_words.txt', 'r')

    # pul the file contents into memory
    flagged_words = temp.readlines()

    # iterate through each word to format it
    for word in range(len(flagged_words)):

        # convert each word into a list object
        flagged_words[word] = eval(flagged_words[word])

        # add the word ID to the list
        flagged_words[word].append(flagged_words[word][0])

        # add the word to the list. replace all of the letters with astrexes ' * '
        # except for the first letter
        flagged_words[word][0] = flagged_words[word][0][0] + '*' * (len(flagged_words[word][0]) - 1)

    # serve the HTML file
    return render_template('admin_words_flagged.html', words=flagged_words, rank=int(rank), mode='banned')


@app.route('/admin/words/banned/add', methods=['post'])
def admin_words_banned_add():
    # this page allows the user to add banned words

    # get information about hte logged in user
    user = users.get_info(session['user'])

    # get the users rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this page
    if rank < 3: # admin +
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get the word from the HTML form in title case
    word = str(request.form['word']).title()

    # open the file containing the current banned words
    temp = open(os.getcwd() + '/lookalive/security/banned_words.txt', 'r')

    # pull the file contenst into memory
    devs = temp.readlines()

    # close the file
    temp.close()

    # iterate through each word in the file removing the EOL chars
    for dev in range(len(devs)):
        devs[dev] = eval(devs[dev].strip('\n'))

    # add the banned word, as well as the ID of the banned word to the array
    devs.append([word, len(devs)])

    # sort the array based on the 1st indes (the word)
    dev_array = things.sort_index(devs, 1)

    # open the text file containing the banned words in write mode
    dev_file = open(os.getcwd() + '/lookalive/security/banned_words.txt', 'w')

    # iterare through each banned word
    for dev in dev_array:

        # write the word to the file
        dev_file.write(str(dev) + '\n')

    # save and close the file
    dev_file.close()

    # write to the log
    log.write_log(user[6], "Added '{}' To The Banned Words".format(word))

    # redirect the user to the list of banned words
    return redirect('/admin/words/banned')


@app.route('/admin/words/banned/delete/<word_id>')
def admin_words_banned_delete(word_id):
    # this page deletes a banned word from the system

    # get info about the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if hte usser can access this page
    if rank < 3: # Admin+
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the text file containing the banned words
    temp = open(os.getcwd() + '/lookalive/security/banned_words.txt', 'r')

    # pull the file contents into memory
    devs = temp.readlines()

    # close the file
    temp.close()

    # create a variable to store the index of the word to delete
    del_index = None

    # iterate through all of the banned words
    for dev in range(len(devs)):

        # convert the line into a proper list, nad remove the EOL character
        devs[dev] = eval(devs[dev].strip('\n'))

        # check if the ID of the word matahces the one that is requestioed to be
        # deleted
        if int(devs[dev][1]) == int(word_id):

            # if it is, update the index variable
            del_index = dev

    # save the word that will be deleted
    word = devs[del_index][0]

    # delete the word
    del devs[del_index]

    # sort the array of words based off the 1st index (the word)
    dev_array = things.sort_index(devs, 1)

    # open the file containing the banned words in write mode
    dev_file = open(os.getcwd() + '/lookalive/security/banned_words.txt', 'w')

    # iterate through each line in the array of words
    for dev in dev_array:

        # write each line to the file of banned words
        dev_file.write(str(dev) + '\n')

    # save and close the file
    dev_file.close()

    # write to the server lof
    log.write_log(user[6], "Deleted '{}' From The Banned Words".format(word))

    # return the user back to the list of banned words
    return redirect('/admin/words/banned')


@app.route('/admin/words/messages')
def admin_words_messages():
    # this page allows the user to view the messages containing flagged words
    # here the user can ignore, or delete the post

    # get info on hte logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access the page
    if rank < 1: # Jr. Mod+
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get a list of the flagged posts
    flagged_words = comment.get_flagged_posts()

    # serve the HTML file
    return render_template('admin_words_message.html', flagged_words=flagged_words)


@app.route('/admin/words/message/ignore/<message_id>')
def admin_words_messages_ignore(message_id):
    # this page allows users to ignore a flagged message

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 2: # Moderator+
        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Moderator", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # ignor the post
    word = comment.ignore_post(int(message_id))

    # write to the log file
    log.write_log(user[6], "Ignored Flagged Message '{}' (ID: {})".format(word, message_id))

    # refirect hte user back to the page to view the flagged messages
    return redirect('/admin/words/messages')


@app.route('/admin/words/message/delete/<message_id>')
def admin_words_messages_delete(message_id):
    # this page allows a user to delete a message

    # get information about the logged in user
    user = users.get_info(session['user'])

    # get teh user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this rescource
    if rank < 2: # Moderator+

        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Moderator", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # delete the comment from the server
    word = comment.delete_comment(int(message_id))

    # write to the log file
    log.write_log(user[6], "Deleted  Flagged Message '{}' (ID: {})".format(word, message_id))

    # redirect the user to the list of messages
    return redirect('/admin/words/messages')


@app.route('/admin/team')
def admin_team():
    # this page allows the user to view the team members, as well asd dev tesers

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this rescource
    if rank < 1: # Jr Mod +

        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get a list of the team member text files
    team_files = os.listdir(os.getcwd() + '/lookalive/team')

    # create an empty list. this list will contain the valid team member file
    team = []

    # iterate through the list of team files
    for file in team_files:

        # check if the file name starts with a ' _ '
        if file.startswith('_') is False:

            # if it does not, it is ok to use as a team file
            # open the file
            temp = open(os.getcwd() + '/lookalive/team/' + file, 'r')

            # add the contents of the file to the empty team list
            team.append(temp.readlines())

    # flip the array (so Nick's name appears first)
    team.reverse()

    # iterart through each team member to format them
    for member in team:
        # replace the 3rd index with the user's file extension based on provideed UUID
        member[3] = users.get_icon_ext(str(member[1]).rstrip('\n'))

    # now on the the dev testers

    # open the dev tester file
    temp = open(os.getcwd() + '/lookalive/team/_dev.txt', 'r')

    # pull the contents of the file into memory
    dev = temp.readlines()

    # close the text file
    temp.close()

    # iterste throug each dev tester
    for tester in range(len(dev)):

        # conbvert their line from a str to list, adn remove the EOL char
        dev[tester] = eval(dev[tester].rstrip('\n'))

    # iterate through the list of members
    for members in range(len(team)):

        # iterart through each line in each member
        for line in range(len(team[members])):

            # format the line by removing teh EOL chars, and the Carrage Return char
            team[members][line] = team[members][line].rstrip('\n').rstrip('\r')

    # serve the HTML file
    return render_template('admin_team.html', team=team, dev=dev)


@app.route('/admin/team/bio/<uuid>')
def admin_team_bio(uuid):
    # this page displays the biography of a person on the development team

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the rank of the user
    rank = users.get_rank_id(user[6])

    # check if the user can access this page
    if rank < 1: # Jr Mod +

        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get a list of all of the team member files
    team_files = os.listdir(os.getcwd() + '/lookalive/team')

    # create a list to store the data of each member
    team = []

    # iteratwe through all of the files
    for file in team_files:

        # check if the file begins with a ' _ '
        if file.startswith('_') is False:

            # if it does not, open the file
            temp = open(os.getcwd() + '/lookalive/team/' + file, 'r')

            # add the contents to the empty list
            team.append(temp.readlines())

    # iterate through each member
    for member in team:

        # check if the member's UUID is the same as the requested ID
        if str(member[1].rstrip('\n')) == str(uuid):

            # if it is, break out of the loop
            break

    # serve the HTML file
    return render_template('admin_team_bio.html', member=member)


@app.route('/admin/team_member/<uuid>')
def admin_team_member(uuid):
    # this page allows a user to edit a team member. this page can only
    # be accessed by a the user who is the team member

    # get info about hte user
    user = users.get_info(session['user'])

    # get the rank of hte user
    rank = users.get_rank_id(user[6])

    # check if hte user can access this page
    if rank < 1: # jr. mod+

        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get info about the logged in user
    user = users.get_info(session['user'])

    # check if the UUID of the user matches the UUID of the requested user
    if str(user[6]) != str(uuid):

        # if it does not, return them to the prevoiusly viewed page
        flash(['Users Can Not Edit The Team Piece Of Other Users', 0])
        return redirect(request.referrer)

    # get a list of the team member files
    team_files = os.listdir(os.getcwd() + '/lookalive/team')

    # create an empty list for all of the team members
    team = []

    # iyterate throiugh all of the team files
    for file in team_files:

        # check if the file starts with ' _ '
        if file.startswith('_') is False:

            # if it does not, add the file path to the list of users
            team.append(os.getcwd() + '/lookalive/team/' + file)

    # for now, set the file name to "None" this allows for a check to see if hte
    # requested user exitst
    file_name = 'None'

    # iterate througt each member in the team
    for member in team:

        # get the file contents of each file
        file_intestine = things.format_file(member)

        # get the first index of the file, and remove the EOL char.
        # check if it matches the requested UUID
        if file_intestine[1].rstrip('\r') == str(uuid):

            # if it matches, set the file variable to the name of the member
            file_name = member

    # serve the HTML file
    return render_template('admin_team_member.html', info=things.format_file(file_name))


@app.route('/admin/team_member/<uuid>/go', methods=['POST'])
def admin_team_member_update(uuid):
    # this page updates the team member page

    # get info about the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access the rescource
    if rank < 1: # jr. mod+

        # if they can not, return them to the prevoiusly viewed page
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get info about the logged in user
    user = users.get_info(session['user'])

    # check if the UUID of the logged in user, and requested user match
    if str(user[6]) != str(uuid):
        # if they do not, return them to the prevoiusly viewed page
        flash(['Users Can Only Edit The Team Piece Of Other Users', 0])
        return redirect(request.referrer)

    # get a list of the team files
    team_files = os.listdir(os.getcwd() + '/lookalive/team')

    # create an empty variable to store the team files
    team = []

    # iterate through each of the team files
    for file in team_files:

        # check if the filename starts with a ' _ '
        if file.startswith('_') is False:

            # if it does not, add the file name to the empty list
            team.append(os.getcwd() + '/lookalive/team/' + file)

    # set the file name to 'None'
    # this is to allow for no file found detection
    file_name = 'None'

    # iterate through each team member
    for member in team:

        # get the contents of each file
        file_intestine = things.format_file(member)

        # check if the UUID in the filke match the UUID that is requested
        if file_intestine[1].rstrip('\r') == str(uuid):

            # if it does match, set hte filke name to the member name
            file_name = member

    # get form fields from the HTML file
    name = request.form['name']                 # name
    new_uuid = request.form['uuid']             # UUID
    title = request.form['title']               # job title
    extension = request.form['extension']       # icon file extensoin
    description = request.form['description']   # member description

    # check if the form field 'name' is nothing
    if name != "":

        # if it is not, overwrite the field
        file_intestine[0] = str(name)

    # check if the form field 'UUID' is nothing
    if new_uuid != "":

        # if it is not, overwrite the field
        file_intestine[1] = str(new_uuid)

    # check if the form field 'title' is nothing
    if title != "":

        # if it is not, overwrite the fieldv
        file_intestine[2] = str(title)

    # check if the form field 'image extension' is nothing
    if extension != "":

        # if it is not, overwrite the field
        file_intestine[3] = str(extension)

    # check if the form field 'description' is nothing
    if description != "":

        # if it is not, overwrite the field

        # split the string into a list at every EOL character
        description = description.split('\n')

        # delete the entire current description
        del file_intestine[4:]

        # uterate through each line of the new desc
        for line in range(len(description)):

            # add each line to the file
            file_intestine.append(str(description[line]))

    # rewrite the file with the updated text
    things.write_list_to_file(file_name, file_intestine)

    # alert hte user of the sucsess through the flash engine
    flash("The Team Member Has Been Sucsessfuly Updated!")

    # write to the log file
    log.write_log(user[6], "Updated Their Team Page")

    # redirect the user to the team page
    return redirect('/admin/team')


@app.route('/admin/team/dev_tester/add', methods=['POST'])
def admin_team_dev_add():
    # this page allows the addition of a dev tester

    # get info about the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 3: # Admin+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get the fields from the HTML form
    name = str(request.form['name'])    # the user's name
    uuid = int(request.form['uuid'])    # the user's UUID

    # open the dev tester file
    temp = open(os.getcwd() + '/lookalive/team/_dev.txt', 'r')

    # pull the contents into memory
    devs = temp.readlines()

    # close the file
    temp.close()

    # iterate thriugh each dev tester
    for dev in range(len(devs)):

        # convert the line into a formatted list, and remove the EOL char
        devs[dev] = eval(devs[dev].strip('\n'))

    # add the dev tester to the list of testers
    devs.append([name, uuid])

    # sort the array based off the 1st index (UUID)
    dev_array = things.sort_index(devs, 1)

    # open the dev tester file in write mode
    dev_file = open(os.getcwd() + '/lookalive/team/_dev.txt', 'w')

    # iterate through all of the dev testers
    for dev in dev_array:

        # write each tester to the file
        dev_file.write(str(dev) + '\n')

    # close the file
    dev_file.close()

    # write to the log
    log.write_log(user[6], "Added Dev Tester: '{}' ({})".format(name, uuid))

    # redirect the user to the team page
    return redirect('/admin/team')


@app.route('/admin/team/dev_tester/delete/<dev_id>')
def admin_team_dev_delete_id(dev_id):
    # this page allows the user to delete a user

    # get info about the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 3: # Admin+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the dev tester text file
    temp = open(os.getcwd() + '/lookalive/team/_dev.txt', 'r')

    # pull the contents into memory
    devs = temp.readlines()

    # close the file
    temp.close()

    # create a variable to store the index of the dev tester to be deleted
    del_index = None

    # iterate through each dev tester
    for dev in range(len(devs)):

        # format the tester to a list, and remove the EOL char
        devs[dev] = eval(devs[dev].strip('\n'))

        # check if the current tester's UUID matches the requested UUID
        if int(devs[dev][1]) == int(dev_id):

            # update the deletion index
            del_index = dev

    # save the tester that will soon be deleted
    tester = devs[del_index]

    # delete the tester
    del devs[del_index]

    # sort the array of testers based on the 1st index (the UUID)
    dev_array = things.sort_index(devs, 1)

    # open the dev tester file in write mode
    dev_file = open(os.getcwd() + '/lookalive/team/_dev.txt', 'w')

    # iterate through the dev tester array
    for dev in dev_array:

        # write each tester to the file
        dev_file.write(str(dev) + '\n')

    # save and close the dev tester file
    dev_file.close()

    # write to the log
    log.write_log(user[6], "Deleted Dev Tester: '{}' ({})".format(tester[0], dev_id))

    # redirect the user to the team page
    return redirect('/admin/team')


@app.route('/admin/help/questions')
def admin_help_questions():
    # this page allows the user to view the questions asked by users

    # get info about the logged in user
    user = users.get_info(session['user'])

    # get the rank of the user
    rank = users.get_rank_id(user[6])

    # check if the user has permission to use this page
    if rank < 1: # jr. Mod+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the questions file, and pull the contents into memory (IN 1 LINE THIS TIME!!!)
    file_data = open(os.getcwd() + '/lookalive/help/question.txt', 'r').readlines()

    # flip the file so newest are first
    file_data.reverse()

    # iterat through each question in storagew
    for line in range(len(file_data)):

        # convert each line to a list, and remove the EOL char
        file_data[line] = eval(file_data[line].strip('\n'))

    # serve the HTML file
    return render_template('admin_questions.html', questions=file_data)


@app.route('/admin/help/questions/delete/<message_id>')
def admin_help_question_delete(message_id):
    # this page allows the user to delete a question from the server

    # get info about the user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this page
    if rank < 2: # moderator+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Moderator", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the file containing the questions
    file_data = open(os.getcwd() + '/lookalive/help/question.txt', 'r').readlines()

    # flip the array in teh file to make the most popular account go first
    file_data.reverse()

    # iterate through the file
    for line in range(len(file_data)):

        # format each line into a list, and remove the EOL char
        file_data[line] = eval(file_data[line].strip('\n'))

    # this variable will store the index of the comment to be deleted
    index = None

    # iterate through the file again
    for line in range(len(file_data)):

        # check if the question ID matches the requested ID
        if str(file_data[line][0] ) == str(message_id):

            # if they do, set the index variable
            index = line

            # break out of the loop
            break

    # save the question that will be deleted
    question = file_data[index]

    # delete the question
    del file_data[index]

    # open the file with the questions in write mode
    new_file = open(os.getcwd() + '/lookalive/help/question.txt', 'w')

    # iterate throught the qustions
    for line in file_data:

        # write each one to the file
        new_file.write(str(line).rstrip('\n') + "\n")

    # save and close the file
    new_file.close()

    # write to the log
    log.write_log(user[6], "Deleted {}'s Question: '{}' ({})".format(question[1], question[2], question[0]))

    # redirect the user back to the page they last viewed
    return redirect(request.referrer)


@app.route('/admin/help/faq')
def admin_help_faq():
    # this page allows the user to edit the FAQ

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this page
    if rank < 1: # jr Mod+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the FAQ file
    faq = open(os.getcwd() + '/lookalive/help/faq.txt', 'r')

    # pull the file contents into memory
    faq = faq.readlines()

    # iterate through the file
    for line in range(len(faq)):
        # remove all of the tab characters
        faq[line] = faq[line].strip('\t')

        # remove the EOL chars
        faq[line] = faq[line].strip('\n')

        # remove the redundant spaces
        faq[line] = faq[line].strip(' ')

    # break the faq down into a list at every EOL char
    faq = '\n'.join(faq)

    # Serve the HTML file
    return render_template('admin_help_faq.html', faq=faq)


@app.route('/admin/help/faq/update', methods=['POST'])
def admin_help_faq_update():
    # this page handles an update to the FAQ a user might make

    # get info on logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 2: # Moderator+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Moderator", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the FAQ file in write mode
    faq_file = open(os.getcwd() + '/lookalive/help/faq.txt', 'w')

    # get the faq file from the HTML form (works like a text editor)
    # cast it to a list, and remove the carrage return chars
    update = str(request.form['new_faq']).rstrip('\r')

    # split the text into a list at every EOL char
    update = update.split('\n')

    # iterate through the new FAQ
    for line in update:

        # write each line to the file
        faq_file.write(line.rstrip('\r') + '\n')

    # save and close the file
    faq_file.close()

    # write to the log
    log.write_log(user[6], "Updated The FAQ")

    # return the user to the FAQ page
    return redirect('/admin/help/faq')


@app.route('/admin/help/contact')
def admin_help_contact():
    # this page alolows the the user to update thje contact page

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this rescource
    if rank < 1: # jr Mod+
        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the contact file
    contact = open(os.getcwd() + '/lookalive/help/contact.txt', 'r')

    # pull the file contents into memory
    contact = contact.readlines()

    # iterate through each line in the file
    for line in range(len(contact)):

        # remove all tab characters
        contact[line] = contact[line].strip('\t')

        # remove the EOL characters
        contact[line] = contact[line].strip('\n')

        # remove redundant spaces
        contact[line] = contact[line].strip(' ')

    # join the text file to a list at every remaining EOL char
    contact = '\n'.join(contact)

    # serve the HTML file
    return render_template('admin_help_contact.html', contact=contact)


@app.route('/admin/help/contact/update', methods=['POST'])
def admin_help_contact_update():
    # this page allows the user to update the contact info

    # get info about the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this rescource
    if rank < 3: # admin+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Admin", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # open the contacts text file
    cont_file = open(os.getcwd() + '/lookalive/help/contact.txt', 'w')

    # get the new file from the HTML form (works like a text editor)
    # cast to str, anre remove all carrage return chars
    update = str(request.form['new_faq']).rstrip('\r')

    # split hte text up by the EOL Chars
    update = update.split('\n')

    # iterate through the text
    for line in update:

        # write the line to the text file, removing all carrage return chars
        cont_file.write(line.rstrip('\r') + '\n')

    # save and close the file
    cont_file.close()

    # write to the lof
    log.write_log(user[6], "Updated The Contact Information")

    # return the user to the contacts page
    return redirect('/admin/help/contact')


@app.route('/admin/cool_page')
def admin_owner_cool_page():
    # this is the cool page that only owners have access to

    # get info about the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 4: # owner+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Owner", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # redirect the user to the best page in the website
    return redirect('http://www.eatwisconsincheese.com/EatWisconsinCheese/media/content/hero%20images/hero-cheese.png')


@app.route('/admin/settings')
def admin_owner_settings():
    # this page allows the user to make updates to the website settings

    # get info on the user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user has permission to use this page
    if rank < 4: # Owner+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Owner", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get the current settings
    current_settings = config.get_current()

    # get all of the presets
    all_presets = preset.get_presets_id()

    # sort the presets alphapbetricaly
    all_presets.sort()

    # serve the HTML file
    return render_template('admin_owner_settings.html', current_settings=current_settings, all_presets=all_presets)


@app.route('/admin/settings/go', methods=['POST'])
def admin_owner_settings_update():
    # this page allows the user to summit changes to the settings

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 4: # Owner+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Owner", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # get the properties from the HTML form
    popular_cap = request.form['popular_cap']                   # the amount of popular posts to display
    special_event = request.form['special_event']               # the special login event
    banned = request.form['banned']                             # the message to display when a banned user attems a disallowed acion
    preset_id = request.form['site_preset']                     # the website display preset
    popular_follower_cap = request.form['popular_follower_cap'] # the minimum amount of followers needed to be a 'popular user'

    motd = request.form['selectbasic']                          # the MOTD ID

    # MOTD IDs
    # 1: Wacky Holiday
    # 2: custom message

    # check if the MOTD ID is 2
    if str(motd) == '2':
        # if it is, a custom message is used
        # get the custom message text box value as the MOTD
        motd = str(request.form['other'])

    # get the banner style for the MOTD
    motd_mode = request.form['motd_mode']

    # preset overides all other settings. check if the preset ID is not 0
    if preset_id != '0':

        # get the properties of the current preset
        preset_data = preset.get_preset_props(int(preset_id))

        # overwrite settings with the preset value
        special_event = preset_data['login_event']

    # create a list of the updated settings
    updated_settings = [popular_cap, special_event, banned, preset_id, popular_follower_cap, motd, motd_mode]

    # write the updates
    config.update_current(updated_settings)

    # alert the user with the custom flash engine
    flash("The Settings Have Been Sucsessfuly Appled!")

    # write to the log
    log.write_log(user[6], "Changed Some Advanced Website Settings")

    # redirect the user to the page they viewed last
    return redirect(request.referrer)


@app.route('/admin/log')
def admin_log():
    # this page allows the user to view the control pannel log

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this rescourfce
    if rank < 1: # jr Mod+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # serve the HTML file
    return render_template('display_list.html', display_list=things.read_file('lookalive/security/log.txt'), page_title="Website Log")


@app.route('/admin/log/clear')
def admin_log_clear():
    # this page allows the user to clear the log

    # get info on logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user can access this rescource
    if rank < 4: # Owner+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Owner", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # clear the log
    log.clear_log()

    # write:
    # ****************************************************************
    # [Datetime] (Username - UUID) : Cleared The Log
    # ****************************************************************
    # to the log
    log.breaker('*')
    log.write_log(user[6], "Cleared The Log")
    log.breaker('*')

    # alert the user of the updaye
    flash("The Log Has Been Cleared.")

    # return the user to the perviously viewed page
    return redirect(request.referrer)


@app.route('/admin/popular_list')
def admin_popular_list():
    # this page allows the user to view the popular users

    # get info on the logged in user
    user = users.get_info(session['user'])

    # get the user's rank
    rank = users.get_rank_id(user[6])

    # check if the user may access this page
    if rank < 1: # Jr. Mod+

        # If they can not, redirect the user to the last page they visited
        flash(['Only Users With The Rank "Jr. Mod", And Above Can Use This Feature', 0])
        return redirect(request.referrer)

    # serve the HTML file
    return render_template('admin_popular_users_list.html', popular_users=users.get_display_popular())


# this page is to test errors
@app.route('/500')
def error_page():
    # this page intentionaly throws an error,
    # so the error 500 page can be tested

    # it returns the string of 1 / 0
    return str(1/0)


# ISE
@app.errorhandler(500)
def server_error(e):
    # this is the page that catches all 500 status codes

    # attempt to get info on the logged in user
    try:
        # get the info
        user = users.get_info(session['user'])

    except KeyError:
        # if it fails because the account does not extist, create an empty
        # 10 item list as the user object
        user = range(10)

    # alert the user with the custom flash engine
    flash(["It Is Christopher's Fault! (Actualy The Duck's Fault)", 1])

    try:
        # attempt to serve the HTML file
        return render_template('500.html', name=user[0], uuid=user[6], ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), error=e)
    except:

        # if any errors occour, serve the HTML file with no parameters
        return render_template('500.html')


# not found
@app.errorhandler(404)
def page_not_found(e):
    # this page handles 404 errors

    try:
        # attempt to get info on the logded in user
        user = users.get_info(session['user'])

    except KeyError:
        # if this fails generate a list with 10 items
        user = range(10)

    # alert the user of the failure
    flash(["It Is Nick's Fault!", 1])

    # serve the HTML file.
    return render_template('404.html', name=user[0], uuid=user[6], ext=users.get_icon_ext(user[6]), unseen=message.get_unseen_messages(user[6]), notify=notification.get_notifications_number(user[6]), error=e)

# App pages

# get all posts
@app.route('/get_post_data')
def index_reload():
    # this function returns all of the posts stored on the server as a unformatted
    # list. this is to allow external access to the post for something like an app?

    # start by getting all of the server's posts
    posts = comment.get_comments()

    # if there are none, use an empty list
    if posts is None:
        posts = []

    # return the list as a string
    return str(posts)


@app.route('/login/user/<username>/<password>')
def external_login(username, password):
    # this function returns 'True' if the variables make up a valid account.
    # if the account is not valid, it returns false.
    # this is for external website log ins

    # using the 'users' module, check if the accound exists
    if users.login(username, password):
        # if the accound does exist, return the user's UUID
        return str(users.get_user_uuid(username))
    else:
        # if the account does not exist, return 'False'
        return 'False'


def out(message):
    # this function writes the message defined as a paramter to "out.txt"

    # open the file in write mode
    temp = open('out.txt', 'w')

    # write to the file
    temp.write(message)

    # save and close the file
    temp.close()


def timeStamped(fname, fmt='%Y-%m-%d %H-%M-%S {fname}'):
    # this function returns a time stamp with the datetime module

    return datetime.datetime.now().strftime(fmt).format(fname=fname)

def get_balloon_array(number):
    # get an array of balloonns to spawn

    # check if the current event or preset event is not 1
    if config.special_event() != 1 or preset.get_preset_props()['login_event'] != 1:

        # if either are not 1, the balloons are not wanted.
        # return a blank lisrt
        return []

    # create an empty list to populate with balloon spawns
    balloons = []

    # itterate 'number' times here
    for balloon in range(number):

        # add a balloon spawn object to the array
        # percent x, image, file ext, speed
        balloons.append([random.randint(10, 90), 'static/images/special/balloons/balloon_' + str(random.randint(0, len(os.listdir(os.getcwd() + '/lookalive/static/images/special/balloons')) - 1)) + '.png', random.uniform(1.0, 3.5)])

    # return the array of balloon spawn objects
    return balloons


def get_snow_flake_array(number):
    # this function returns an array of snowflakes

    # check if the current event or preset event is not 2
    if config.special_event() != 2 or preset.get_preset_props()['login_event'] != 2:

        # if either are 2, return a blank list
        return []

    # create a blank array to store snowflakes
    balloons = []

    # iterarate through the array of requested snowflakes
    for balloon in range(number):

        # add a snowflake to the array
        # x percent, image, file ext, speed
        balloons.append([random.randint(10, 90), 'static/images/special/snow/flake_' + str(random.randint(0, len(os.listdir(os.getcwd() + '/lookalive/static/images/special/snow')) - 1)) + '.png', random.uniform(1.0, 3.5)])

    # return the array
    return balloons

