import users

def all_follow_lookalive_account(user_id):
    uuids = users.get_all_users_uuid()

    for uuid in uuids:
        if int(uuid) != user_id:
            users.follow(uuid, user_id, False)

all_follow_lookalive_account(1)
all_follow_lookalive_account(0)