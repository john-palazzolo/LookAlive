import time
import difflib
import os
import shutil

def copy_rename(old_file_name, new_file_name):
    # source = old_file
    # destination = new_file

    # shutil.copy(old_file + old_name,destination)

    # -----------------------------------

    # src_dir= os.curdir
    # dst_dir= os.path.join(os.curdir , "subfolder")
    # src_file = os.path.join(src_dir, old_file_name)
    # shutil.copy(src_file,dst_dir)

    # dst_file = os.path.join(dst_dir, old_file_name)
    # new_dst_file_name = os.path.join(dst_dir, new_file_name)
    # os.rename(dst_file, new_dst_file_name)

    shutil.copyfile(old_file_name, new_file_name)

def get_time():
    return time.time()


def sort_index(array, index):

    array.sort(key=lambda x: x[index])
    return array


def match_percent(word_1, word_2):
    percent = difflib.SequenceMatcher(None, word_1, word_2).ratio()
    percent *= 100

    return percent


def match_list(word, word_list):
    master = []
    for item in word_list:
        print item
        master.append([round(match_percent(word, item[0]), 1), item[0], item[1], item[2], item[3], item[4]])

    master = sorted(master)
    master.reverse()

    return master


def extensionify(path):
    filename, file_extension = os.path.splitext(path)
    return filename, file_extension


def format_file(file_name):
    temp = open(file_name, 'r')
    file = temp.readlines()

    for line in range(len(file)):
        file[line] = file[line].rstrip('\n')

    temp.close()

    return file


def write_list_to_file(file_name, write_list):
    the_file = open(file_name, 'w')

    for line in write_list:
        the_file.write(str(line) + '\n')

    the_file.close()


def percent_change(text, percent, replace_char):
    percent = percent / 100.0
    replace_amount = int(round(percent * len(text), 0))

    text_list = list(text)
    del text_list[replace_amount:]

    for missing in range(replace_amount):
        text_list.append(replace_char)

    text = ''.join(text_list)
    return text


def read_file(filename):
    temp = open(filename)
    data = temp.readlines()
    temp.close()

    for line in range(len(data)):
        data[line] = str(data[line]).rstrip('\n')

    return data


def clear_file(filename):
    temp = open(filename, 'w')
    temp.close()

