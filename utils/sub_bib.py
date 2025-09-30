import utils.file_parser as file_parser
import utils.file_generator as file_generator

from objects import BibFile, Reference, Comment


def sub_bib(file: BibFile, entry_types: list) -> BibFile:
    """
    Returns a grouped File object which contains References
    which have entry types in the passed entry_types list
    """
    new_file = BibFile(file.file_name)
    previous_added = False  # Flag to ensure that only relevant comments get added.
    for entry in file.content:
        if type(entry) is Reference:
            if entry.entry_type in entry_types:
                new_file.content.append(entry)
                previous_added = True
            else:
                previous_added = False
        elif type(entry) is Comment:
            if previous_added:
                new_file.content.append(entry)
        else:
            new_file.content.append(entry)

    return new_file


# JUST FOR TESTING       
if __name__ == "__main__":
    test_file = file_parser.parse_bib("../bibtests.bib", True)
    sub_file = sub_bib(test_file, ["article"])
    file_generator.generate_bib(sub_file, sub_file.file_name, 15)
