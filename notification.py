import ast


def get_notifications(uuid):
    data = __open_file(uuid)

    for note in range(len(data)):
        try:
            print data[note][0], type(data[note][0])
            data[note][0] = ast.literal_eval(data[note][0])
        except SyntaxError:
            pass


    # data.reverse()
    print data
    return data


def get_notifications_number(uuid):
    data = __open_file(uuid)
    # data.reverse()
    return len(data)


def delete_notification(uuid, delete_id):
    if str(delete_id) == 'all':
        __rewrite_file(uuid, [])
    else:
        uuid = int(uuid)
        delete_id = int(delete_id)
        notification_file = __open_file(uuid)

        del notification_file[delete_id]

        notification_file = __extract_id_from_list(notification_file)

        __rewrite_file(uuid, notification_file)


def add_notification(uuid, text, send_uuid):
    notification_file = __open_file(uuid)

    notification_file.insert(0, str([text, send_uuid]))

    __rewrite_file(uuid, notification_file)

def __open_file(uuid):
    temp = open('lookalive/notifications/{}.txt'.format(uuid), 'r')
    file_data = temp.readlines()
    temp.close()

    for line in range(len(file_data)):
        file_data[line] = [file_data[line].rstrip('\n'), line]

    return file_data


def __rewrite_file(uuid, new_data):
    temp = open('lookalive/notifications/{}.txt'.format(uuid), 'w')

    for item in new_data:
        if type(item) == type(['sup']):
            temp.write(str(item[0]) + '\n')
        else:
            temp.write(str(item) + '\n')

    temp.close()


def __extract_id_from_list(notification_file):
    output = []
    for line in notification_file:
        output.append(line[0])

    return output


def new_user(uuid):
    temp = open('lookalive/notifications/{}.txt'.format(uuid), 'w')
    temp.close()


