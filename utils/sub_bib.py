import json

import utils.file_parser as file_parser
import utils.file_generator as file_generator

from objects import BibFile, Reference


def filter_entry_types(file: BibFile, entry_types: list) -> list:
    """
    Returns a list which contains References
    which have entry types in the passed entry_types list
    """
    array = []
    for entry in file.content:
        if type(entry) is Reference:
            if entry.entry_type in entry_types:
                array.append(entry)
        # else:
        #     # Always add all other types (string, comment and preamble)
        #     array.append(entry)
        #TODO: COMMENTS?

    return array


def filter_tags(file: BibFile, tags: list) -> list:
    """
    Returns a list with all references that have a tag from the tags file
    :param file: the input file
    :param tags: a list of tags
    :return: the output list
    """
    with open('tags.json') as tags_data:
        tags_dict = json.load(tags_data)

    relevant_cite_keys = set()
    for tag, cite_keys in tags_dict.items():
        if tag in tags:
            relevant_cite_keys.update(cite_keys)

    array = []
    for entry in file.content:
        if type(entry) is Reference:
            if entry.cite_key in relevant_cite_keys:
                array.append(entry)
        # else:
        #     # Always add all other types (string, comment and preamble)
        #     array.append(entry)
        #TODO: COMMENTS?

    return array


# JUST FOR TESTING
if __name__ == "__main__":
    test_file = file_parser.parse_bib("../biblatex-examples.bib", True)
    article_file = filter_entry_types(test_file, ["article", "collection"])
    file_generator.generate_bib(article_file, "article+collection-examples.bib", 15)
