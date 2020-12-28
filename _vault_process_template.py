import glob
import os
from collections import Counter

from dotenv import load_dotenv
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


def traverse_files():
    """
    Reads all files from the obsidian vault
    The path is read from te environment variable `OBSIDIAN_VAULT`
    It needs to contain an absolut path (tilde is not expanded)

    :return: Tuple with results
    :rtype: Tuple
    """
    result = None

    root_dir = os.getenv("OBSIDIAN_VAULT")
    # Add path separator at the end if needed
    # root_dir needs a trailing slash (i.e. /root/dir/)
    if root_dir[-1] != os.path.sep:
        root_dir = root_dir + os.path.sep

    for filename in glob.iglob(root_dir + "**/*.md", recursive=True):
        with open(filename, "r") as file:
            content = file.read()

        try:
            language = detect(content)
        except LangDetectException:
            language = "en"  # Fallback

        if language == "de":
            pass
        else:
            pass

    return result


def count_items(item_list: list) -> list:
    """
    Counts the occurrences of items in the list and sorts it descending
    by count.

    :param item_list:  List with the items to count
    :type item_list: list
    :return: List containing tuples with (item,count)
    :rtype: list
    """
    # Count the items
    counts = Counter(item_list).most_common()

    # Sort them by occurrence
    counts.sort(key=lambda tup: tup[1], reverse=True)

    return counts


def print_stats(info_type: str, count: int, list_: list):
    # """
    # Prints a markdown table to the stdoout.
    #
    # :param info_type: Info Type text in the headline
    # :type info_type: str
    # :param count: Number of items to print
    # :type count: int
    # :param list_: List containing tuples with (item,count)
    # :type list_: list
    # """
    # print(f"## Top {count}", info_type)
    # print()
    #
    # print("| #  | Count | Content                      |")
    # print("|---:|------:|------------------------------|")
    # for i in range(count):
    #     print(f"|{i+1:4}|{list_[i][1]:7}|{list_[i][0]:30}|")
    #
    # print()
    pass


if __name__ == "__main__":
    """
    Script to apply some NLP to your obsidian vault
    The path to the vault is read from te environment variable `OBSIDIAN_VAULT`
    It needs to contain an absolut path (tilde is not expanded)
    """
    load_dotenv(verbose=True)

    tokens = traverse_files()

    stats = count_items(tokens)
    print_stats("Tokens", 10, stats)
