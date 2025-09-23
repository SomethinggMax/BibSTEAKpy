import file_parser
import file_generator

from objects import File, Reference

def sub_bib(file: File, entry_types: list) -> File:
    """
    Returns a grouped File object which contains References
    which have entry types in the passed entry_types list
    """
    new_file = File(file.get_filename())
    for entry_type in entry_types:
        for reference in file.references:
            if reference.entry_type == entry_type:
                new_file.append_reference(reference)
        
    return new_file
        
if __name__ == "__main__":
    test_file = file_parser.parse_bib("bibtests.bib", True)
    sub_file = sub_bib(test_file, ["article"])
    file_generator.generate_bib("biblatex-examples-generated.bib", 15, sub_file)
