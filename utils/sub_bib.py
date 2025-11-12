import utils.file_parser as file_parser
import utils.file_generator as file_generator
from objects import BibFile, Reference
from utils import json_loader


def filter_entry_types(file: BibFile, entry_types: list) -> BibFile:
    """
    Returns a grouped File object which contains References
    which have entry types in the entry_types list
    """
    new_file = BibFile(file.file_path)
    for entry in file.content:
        if type(entry) is Reference:
            if entry.entry_type.lower() in entry_types:
                new_file.content.append(entry)
        else:
            # Always add all other types (string, comment and preamble)
            new_file.content.append(entry)

    return new_file


def filter_tags(file: BibFile, tags: list) -> BibFile:
    """
    Returns a BibFile object with all references that have a tag from the tags list.
    :param file: the input file
    :param tags: a list of tags
    :return: the output file
    """
    tags_dict = json_loader.load_tags()

    relevant_cite_keys = set()
    for tag, cite_keys in tags_dict.items():
        if tag in tags:
            relevant_cite_keys.update(cite_keys)

    new_file = BibFile(file.file_path)
    for entry in file.content:
        if type(entry) is Reference:
            if entry.cite_key in relevant_cite_keys:
                new_file.content.append(entry)
        else:
            # Always add all other types (string, comment and preamble)
            new_file.content.append(entry)

    return new_file


# JUST FOR TESTING
if __name__ == "__main__":
    test_file = file_parser.parse_bib("../bib_files/biblatex-examples.bib")
    article_file = filter_entry_types(test_file, ["article", "collection"])
    file_generator.generate_bib(article_file, "../bib_files/article+collection-examples.bib")

    tagged_sub_file = filter_tags(test_file, ["Computer Science", "Virtual memory and storage"])
    file_generator.generate_bib(tagged_sub_file, "../bib_files/tagged-examples.bib")
