import utils.file_parser as file_parser
import utils.file_generator as file_generator

from objects import BibFile, Reference


def sub_bib(file: BibFile, entry_types: list) -> BibFile:
    """
    Returns a grouped File object which contains References
    which have entry types in the passed entry_types list
    """
    new_file = BibFile(file.file_name)
    for entry_type in entry_types:
        for entry in file.content:
            if entry is Reference:
                if entry.entry_type == entry_type:
                    new_file.content.append(entry)
            else:
                new_file.content.append(entry)

    return new_file


# JUST FOR TESTING       
if __name__ == "__main__":
    test_file = file_parser.parse_bib("bibtests.bib", True)
    sub_file = sub_bib(test_file, ["article"])
    file_generator.generate_bib("biblatex-examples-generated.bib", 15, sub_file)
