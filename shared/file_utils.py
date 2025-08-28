import os
import random
import re
import logging

def get_random_file_id(directory_path):
    """
    Gets a random file id based on the files already in the directory
    Assumes that all files in the directory are only numbers

    :param directory_path: The directory to check for duplicate file ids
    :return: A file id that is not being used
    """
    logging.info("Finding available file id")
    current_file_ids = set()
    for filename in os.listdir(directory_path):
        match = re.match(r"^(\d+)(?:_normalized)?\.", filename)
        if match:
            current_file_ids.add(int(match.group(1)))
    available_ids = set(range(1, 10000)) - current_file_ids
    final_id = random.choice(tuple(available_ids))
    logging.info("Found randomized available file id: %d", final_id)
    return final_id
