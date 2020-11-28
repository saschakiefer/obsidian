import glob
import os
from collections import Counter
from typing import Tuple

from langdetect import detect
from dotenv import load_dotenv
import spacy

# setup spacy
from langdetect.lang_detect_exception import LangDetectException

nlp_de = spacy.load("de_core_news_sm")
nlp_en = spacy.load("en_core_web_sm")

# add some stop words specific for my capturing style
general_stops = {
    "_",
    "#",
    "##",
    "###",
    "####",
    "#####",
    "######",
    "←",
    "→",
    "🙅",
    "♂",
    "🤔",
    "🌳",
    "🌱",
    "✅",
    "*",
    "-",
    "=",
    "|",
    "[",
    "]",
    ">",
    "<",
    "/",
    "\\",
    "{",
    "}",
    "(",
    ")",
    "check todos",
    " ",
    "☀️",
    "☀",
    "📗 log",
    "🌙",
    "10 liegestütz",
    "das heutige highlight",
    "# 🌙 evening reflection",
    "todos",
    "[ ]",
    "[x]",
    "☀️ morning",
    "## 🌙 evening",
    "# 🌙 evening",
}
nlp_de.Defaults.stop_words |= general_stops
nlp_en.Defaults.stop_words |= general_stops


def tokenize_file(content: str) -> Tuple[list, list, list]:
    """
    Tokenizes the file using nlp. It returns the tokens,
    the known nouns and the noun chunks
    :param content: Text content of the file
    :type content: str
    :return: Token list, entity list and noun chunk list
    :rtype: Tuple
    """
    if content == "":
        return [], [], []

    # content = content.lower()  # Some Sort of concistency

    work_content = content.replace("[[", "")  # Remove [[
    work_content = work_content.replace("]]", "")  # Remove [[
    work_content = work_content.replace("\n", " ")  # Remove new line
    work_content = work_content.replace("\t", " ")  # Remove tab
    work_content = work_content.replace("[ ]", "")  # Remove todos checkbox
    work_content = work_content.replace("[x]", "")  # Remove todos checkbox

    # Remove stop words - Language Dependent
    doc = None

    try:
        language = detect(work_content)
    except LangDetectException:
        language = "en"  # Fallback

    if language == "de":
        doc = nlp_de(work_content)
    else:
        doc = nlp_en(work_content)

    # Tokens without stopwords, space, numbers and punctuation
    # For word count, I use the lemma
    tokens = [
        word.lemma_
        for word in doc
        if not doc.vocab[word.text].is_stop
        and word.pos_ not in {"SPACE", "PUNCT", "NUM"}
        and word.lemma_ != "️"
    ]

    entities = [
        ent.text.strip()
        for ent in doc.ents
        if not doc.vocab[ent.text].is_stop and ent.text.strip() != "️"
    ]

    noun_chunks = [
        chunks.text.strip()
        for chunks in doc.noun_chunks
        if not doc.vocab[chunks.text].is_stop and chunks.text.strip() != "️"
    ]

    return tokens, entities, noun_chunks


def get_all_words_in_vault() -> Tuple[list, list, list]:
    """
    Reads all files from the obsidian vault
    The path is read from te environment variable `OBSIDIAN_VAULT`
    It needs to contain an absolut path (tilde is not expanded)

    Cumulates the tokens, entities and noun chunks in separate lists
    :return: Tuple with token list, entity list and noun chunk list
    :rtype: Tuple
    """
    root_dir = os.getenv("OBSIDIAN_VAULT")
    token_list = []
    entity_list = []
    noun_chunk_list = []

    # Add path separator at the end if needed
    # root_dir needs a trailing slash (i.e. /root/dir/)
    if root_dir[-1] != os.path.sep:
        root_dir = root_dir + os.path.sep

    for filename in glob.iglob(root_dir + "**/*.md", recursive=True):
        with open(filename, "r") as file:
            content = file.read()

        file_tokens, file_entities, file_chunks = tokenize_file(content)
        token_list = token_list + file_tokens
        entity_list = entity_list + file_entities
        noun_chunk_list = noun_chunk_list + file_chunks

    return token_list, entity_list, noun_chunk_list


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
    """
    Prints a markdown table to the stdoout.

    :param info_type: Info Type text in the headline
    :type info_type: str
    :param count: Number of items to print
    :type count: int
    :param list_: List containing tuples with (item,count)
    :type list_: list
    """
    print(f"## Top {count}", info_type)
    print()

    print("| #  | Count | Content                      |")
    print("|---:|------:|------------------------------|")
    for i in range(count):
        print(f"|{i+1:4}|{list_[i][1]:7}|{list_[i][0]:30}|")

    print()


if __name__ == "__main__":
    """
    Script to apply some NLP to your obsidian vault
    The path to the vault is read from te environment variable `OBSIDIAN_VAULT`
    It needs to contain an absolut path (tilde is not expanded)
    """
    load_dotenv(verbose=True)

    tokens, entities, chunks = get_all_words_in_vault()

    stats = count_items(tokens)
    print_stats("Tokens", 10, stats)

    stats = count_items(entities)
    print_stats("Entities", 10, stats)

    stats = count_items(chunks)
    print_stats("Noun Chunks", 10, stats)
