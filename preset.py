import config


def __open_file(mode='r'):
    temp = open('/home/lookalive/lookalive/config/presets.txt', mode)

    if mode == 'r':
        presets = temp.readlines()
        temp.close()

        return eval(''.join(presets))

    elif mode == 'w':
        return temp
    else:
        return temp


def get_presets():
    presets = __open_file()
    return presets.keys()


def get_presets_id():
    presets = __open_file()
    preset_keys = presets.keys()
    preset_lst = []

    for each_preset in preset_keys:
        preset_lst.append([each_preset, presets[each_preset]['name']])

    return preset_lst


def get_preset_props(preset_id=None):
    if preset_id is None:
        preset_id = int(config.site_preset())

    presets = __open_file()
    print '-'*64
    print presets
    return presets[str(preset_id)]