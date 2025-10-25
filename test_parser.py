from utils import file_parser
import bibtexparser


def compare_parsing(original_path) -> bool:
    """
    Compares the file_parser with the bibtexparser python library.
    :param original_path: the path of the file to test.
    :return: True if both parsers give the same cite keys and the same number of fields for each reference.
    """
    # Parse with bibtexparser
    parser = bibtexparser.bparser.BibTexParser()
    parser.ignore_nonstandard_types = False
    parser.homogenize_fields = False
    parser.interpolate_strings = False
    with open(original_path, encoding='utf-8') as file:
        bibtexparser_example_file = bibtexparser.load(file, parser)

    # Parse with file_parser
    file_parser_example_file = file_parser.parse_bib(original_path, True)

    # Compare results
    bibtexparser_entries = len(bibtexparser_example_file.entries)
    file_parser_entries = len(file_parser_example_file.get_references())
    if bibtexparser_entries != file_parser_entries:
        print(f"Bibtexparser entries: {bibtexparser_entries}, file_parser entries: {file_parser_entries}")
        return False
    else:
        for entry in bibtexparser_example_file.entries:
            cite_key = entry["ID"]
            if cite_key not in file_parser_example_file.get_cite_keys():
                print(f"Entry with cite key '{cite_key}' is missing in the parsed file.")
                return False
            else:
                file_parser_reference = file_parser_example_file.get_reference_by_key(cite_key)
                file_parser_reference_fields = len(file_parser_reference.get_fields()) - 1
                if file_parser_reference_fields != len(entry):
                    print(f"Entry with cite key '{cite_key}' "
                          f"does not have the same number of fields in the parsed file: "
                          f"{file_parser_reference_fields} != {len(entry)}.")
                    return False
    return True


if __name__ == '__main__':
    bib_examples_original_path = "bib_files/bibtests.bib"
    compare_parsing(bib_examples_original_path)

