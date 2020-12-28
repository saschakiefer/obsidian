import glob
import os
from collections import Counter
import re
from typing import Dict

from dotenv import load_dotenv


def clean_link(link: str) -> str:
    text = link.split("|")[0]
    text = text.split("#^")[0]

    return text


def traverse_files() -> Dict:
    """
    Reads all files from the obsidian vault
    The path is read from te environment variable `OBSIDIAN_VAULT`
    It needs to contain an absolut path (tilde is not expanded)

    :return: Dict with results
    :rtype: Dict
    """
    result = {}
    result["file_names"] = []
    result["existing"] = []
    result["not_existing"] = []

    root_dir = os.getenv("OBSIDIAN_VAULT")
    # Add path separator at the end if needed
    # root_dir needs a trailing slash (i.e. /root/dir/)
    if root_dir[-1] != os.path.sep:
        root_dir = root_dir + os.path.sep

    # Get the filenames upfront, so that we can process them in the real content
    # reading step
    for filename in glob.iglob(root_dir + "**/*.md", recursive=True):
        result["file_names"].append(os.path.basename(filename).split(".")[0])

    #       Regex Fragment      | Meaning
    #       ===================================================================
    #         \[\[              | match starts with [[
    #             (      )      | capturing only parentheses w/o [[ and ]]
    #              [   ]        | match characters that are...
    #               ^\]         | ... any character but a ] (signal for the end)
    #                   +       | ...multiple times
    #                     \]\]  | match ends with ]]
    regex = r"\[\[([^\]]+)\]\]"
    c_regex = re.compile(regex)
    for filename in glob.iglob(root_dir + "**/*.md", recursive=True):
        with open(filename, "r") as file:
            content = file.read()

        links = c_regex.findall(content)

        for link in links:
            link = clean_link(link)

            # Check if link is a date -> discard
            if re.match(r"\d\d\d\d-\d\d-\d\d", link) is not None:
                continue

            # Check if link is a person -> discard
            if link.startswith("@"):
                continue

            if link in result["file_names"]:
                result["existing"].append(link)
            else:
                result["not_existing"].append(link)

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


def print_stats(tokens: Dict):
    print("# Used Links\n")
    print("| #  | Existing Links | Not Existing Links  |")
    print("|---:|-------------------------------|--------------------------------|")

    i = 0
    while True:
        if i < len(tokens["existing_counted"]):
            ec = f'{tokens["existing_counted"][i][0]} ({tokens["existing_counted"][i][1]})'
        else:
            ec = ""

        if i < len(tokens["not_existing_counted"]):
            nec = f'{tokens["not_existing_counted"][i][0]} ({tokens["not_existing_counted"][i][1]})'
        else:
            nec = ""

        print(f"|{i+1:4}|{ec:60}|{nec:60}|")

        i = i + 1
        if i >= max(
            len(tokens["existing_counted"]), len(tokens["not_existing_counted"])
        ):
            break

    print()


if __name__ == "__main__":
    """
    Script to apply some NLP to your obsidian vault
    The path to the vault is read from te environment variable `OBSIDIAN_VAULT`
    It needs to contain an absolut path (tilde is not expanded)
    """
    load_dotenv(verbose=True)

    tokens = traverse_files()

    tokens["existing_counted"] = count_items(tokens["existing"])
    tokens["not_existing_counted"] = count_items(tokens["not_existing"])
    print_stats(tokens)
