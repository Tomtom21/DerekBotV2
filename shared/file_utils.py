import os
import random


def get_random_file_id(directory_path):
    """
    Gets a random file id based on the files already in the directory
    Assumes that all files in the directory are only numbers

    :param directory_path: The directory to check for duplicate file ids
    :return: A file id that is not being used
    """
    current_file_ids = {int(filename.split(".")[0]) for filename in os.listdir(directory_path)}
    available_ids = set(range(1, 10000)) - current_file_ids
    return random.choice(tuple(available_ids))
