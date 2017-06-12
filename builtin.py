import things

# declare module contsatnts
FILENAME = "lookalive/output.txt"


def output(text):
    # this function adds the 'text' parameter to the output file

    # get the contenst of the file with the things module
    total_file = things.read_file(FILENAME)

    # add the text to the file
    total_file.append(text)

    # write the new file to the output file
    things.write_list_to_file(FILENAME, total_file)


def clear_file():
    # this function clears the file

    # clear the file with the things module
    things.clear_file(FILENAME)