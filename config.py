import os


def __open_file(mode='r'):
    temp = open(os.getcwd() + '/lookalive/config/config.txt', mode)

    if mode == 'r':
        config = temp.readlines()
        temp.close()

        return eval(''.join(config))

    elif mode == 'w':
        return temp
    else:
        return temp



def view_all_comments():
    config = __open_file()
    return config['view_all_comments']


def number_of_popular_posts():
    config = __open_file()
    return config['popular_like_results_cap']


def special_event():
    config = __open_file()
    return config['special_event']


def banned_message():
    config = __open_file()
    return config['banned_message']


def site_preset():
    config = __open_file()
    return config['preset_id']


def popular_follower_cap():
    config = __open_file()
    return int(config['popular_follower_cap'])


def motd():
    config = __open_file()
    return config['MOTD']


def motd_mode():
    config = __open_file()
    return config['MOTD_mode']


def get_current():
    values = []

    values.append(view_all_comments())
    values.append(number_of_popular_posts())
    values.append(special_event())
    values.append(banned_message())
    values.append(site_preset())
    values.append(popular_follower_cap())
    values.append(motd())
    values.append(motd_mode())

    return values


def update_current(settings):
    # 'settings' format: [popular_cap, special_event, banned, site_preset, popular_follower_cap, MOTD, MOTD_mode]
    config = __open_file()
    config['popular_like_results_cap'] = int(settings[0])
    config['special_event'] = int(settings[1])
    config['banned_message'] = str(settings[2])
    config['preset_id'] = str(settings[3])
    config['popular_follower_cap'] = int(settings[4])
    try:
        config['MOTD'] = int(settings[5])
    except ValueError:
        config['MOTD'] = str(settings[5])
    config['MOTD_mode'] = int(settings[6])

    config_file = __open_file('w')
    config_file.write(str(config))
    config_file.close()




