import utils.file_parser as file_parser
import utils.file_generator as file_generator

from objects import BibFile, Reference, Comment


def sub_bib(file: BibFile, entry_types: list) -> BibFile:
    """
    Returns a grouped File object which contains References
    which have entry types in the passed entry_types list
    """
    new_file = BibFile(file.file_name)
    comment = False  # Flag to ensure that only relevant comments get added.
    for entry in file.content:
        if type(entry) is Reference:
            if entry.entry_type in entry_types:
                if comment:
                    new_file.content.append(comment)
                new_file.content.append(entry)
            else:
                comment = False
        elif type(entry) is Comment:
            comment = entry
        else:
            new_file.content.append(entry)

    return new_file


# JUST FOR TESTING       
if __name__ == "__main__":
    test_file = file_parser.parse_bib("../biblatex-examples.bib", True)
    sub_file = sub_bib(test_file, ["article", "collection"])
    file_generator.generate_bib(sub_file, sub_file.file_name, 15)
