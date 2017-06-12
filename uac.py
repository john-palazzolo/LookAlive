import config

def get_banned_message(cant_do):
    return config.banned_message().replace('&', cant_do)