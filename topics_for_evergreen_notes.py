import glob
import os
import re
import zipfile
from datetime import datetime

import pandas as pd
import spacy
from dotenv import load_dotenv
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

stop_words_german = pd.read_csv("./resources/german_stopwords.txt", header=None)[
    0
].values.tolist()

cv_german = CountVectorizer(max_df=0.80, min_df=3, stop_words=stop_words_german)

lemmatizer = spacy.load("de_core_news_lg", disable=["parser"])


def traverse_files():
    """
    Reads all files from the obsidian vault
    The path is read from te environment variable `OBSIDIAN_VAULT`
    It needs to contain an absolut path (tilde is not expanded)

    :return: Tuple with results
    :rtype: Tuple
    """
    result = {}
    result["german"] = []
    result["english"] = []

    root_dir = os.getenv("OBSIDIAN_VAULT")
    # Add path separator at the end if needed
    # root_dir needs a trailing slash (i.e. /root/dir/)
    if root_dir[-1] != os.path.sep:
        root_dir = root_dir + os.path.sep

    npr_german = pd.DataFrame(columns=["File", "Language", "Article"])
    npr_english = pd.DataFrame(columns=["File", "Language", "Article"])

    for filename in glob.iglob(root_dir + "🌳 Evergreen Notes/**/*.md", recursive=True):
        if "✍️ Journal" in filename or "🌳 Map of MoC.md" in filename:
            continue

        with open(filename, "r") as file:
            content = file.read()

        try:
            language = detect(content)
        except LangDetectException:
            language = "en"  # Fallback

        if language == "de":
            npr_german = npr_german.append(
                {"File": filename, "Language": language, "Article": content},
                ignore_index=True,
            )
        else:
            npr_english = npr_english.append(
                {"File": filename, "Language": language, "Article": content},
                ignore_index=True,
            )

    result["german"] = npr_german
    result["english"] = npr_english

    # print(npr_german)
    # print(npr_english)

    return result


def get_topics(articles):
    dtm = cv_german.fit_transform(articles["Article"])

    LDA = LatentDirichletAllocation(n_components=100, random_state=42)
    LDA.fit(dtm)

    topics = []
    for index, topic in enumerate(LDA.components_):
        # top = [cv_german.get_feature_names()[i] for i in topic.argsort()[-7:]]
        top_lem = [
            lemmatizer(cv_german.get_feature_names()[i])[0].lemma_
            for i in topic.argsort()[-7:]
        ]

        topics.append(top_lem)

        # print(f"Die TOP-15 Wörter für das Thema #{index}")
        # print(top)
        # print(top_lem)
        # print("\n")

    topic_results = LDA.transform(dtm)
    articles["Topic"] = topic_results.argmax(axis=1)

    # print(topics)
    # print(articles.head(10))

    return articles, topics


def prepend_to_file(articles):
    for index, row in articles["german"].iterrows():
        print("\t", row["File"])

        tags = ""
        for tag in articles["topics_german"][row["Topic"]]:
            tags = ", ".join([tags, f'"#nlp/{tag}"'])

        tags = "tags: [" + tags[2:] + "]"

        # print(tags.rstrip("\r\n") + "\n")

        with open(row["File"], "r+") as file:
            content = file.read()

            # Try to replace the tag
            regex = r"(^tags\:\s.*$)"
            result = re.subn(regex, tags, content, 1, re.MULTILINE)

            # If the tag was overwritten, write the file back
            # Otherwise prepend tags
            if result[1] == 1:
                file.truncate(0)
                file.seek(0, 0)
                file.write(result[0])
            else:
                tags = "---\n" + tags + "\n---\n"
                file.seek(0, 0)
                file.write(tags.rstrip("\r\n") + "\n\n" + content)


def backup_vault():
    timestampStr = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_file = zipfile.ZipFile(
        os.getenv("BACKUP_DIR") + "Obsidian_Backup_" + timestampStr + ".zip",
        "w",
        zipfile.ZIP_DEFLATED,
    )

    for root, dirs, files in os.walk(os.getenv("OBSIDIAN_VAULT")):
        for file in files:
            zip_file.write(os.path.join(root, file))

    zip_file.close()


if __name__ == "__main__":
    """
    Script to apply some NLP to your obsidian vault
    The path to the vault is read from te environment variable `OBSIDIAN_VAULT`
    It needs to contain an absolut path (tilde is not expanded)
    """
    load_dotenv(verbose=True)

    print("Backing Up Vault to", os.getenv("BACKUP_DIR"))
    backup_vault()

    print("Reading articles from", os.getenv("OBSIDIAN_VAULT"))
    articles = traverse_files()

    print("Building Topic List")
    articles["german"], articles["topics_german"] = get_topics(articles["german"])

    print("Adding generated topics to articles")
    prepend_to_file(articles)
