from objects import BibFile, Reference, String
from utils import file_parser, file_generator


def batch_replace(bib_file: BibFile, fields_to_edit: [str], old_string: str, new_string: str) -> BibFile:
    """
    Searches the references for occurrences of the old_string and replaces them with the new_string.
    Only searches the fields given in the fields_to_edit parameter, or all if empty.
    """
    for entry in bib_file.content:
        if type(entry) is Reference:
            fields = entry.get_fields()
            for field_type, data in fields.items():
                if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
                    continue
                if not fields_to_edit:
                    fields[field_type] = data.replace(old_string, new_string)
                elif field_type in fields_to_edit:
                    fields[field_type] = data.replace(old_string, new_string)
    return bib_file


def batch_rename_abbreviation(bib_file: BibFile, old_abbreviation: str, new_abbreviation: str) -> BibFile:
    """
    Rename a String abbreviation in the BibFile.
    """
    for entry in bib_file.content:
        if isinstance(entry, String):
            if entry.abbreviation == old_abbreviation:
                entry.abbreviation = new_abbreviation
        if isinstance(entry, Reference):
            fields = entry.get_fields()
            for field_type, data in fields.items():
                if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
                    continue
                if data == old_abbreviation:
                    fields[field_type] = new_abbreviation
                elif "#" in data:
                    data_list = data.split("#")
                    final_data = ""
                    # Loop over all elements except the last one (to add the #s back)
                    for string in data_list[:-1]:
                        stripped = string.strip()
                        if stripped == old_abbreviation:
                            final_data += new_abbreviation + " # "
                        else:
                            final_data += stripped + " # "

                    # Add the final part of the string.
                    stripped = data_list[-1].strip()
                    if stripped == old_abbreviation:
                        final_data += new_abbreviation
                    else:
                        final_data += stripped

                    fields[field_type] = final_data

    return bib_file


def batch_extend_strings(bib_file: BibFile, abbreviations: [str]) -> BibFile:
    """
    Extends all given abbreviations in the BibFile and removes the Strings from the BibFile.
    Gets the long_form from the String object in the BibFile.
    :param bib_file: input BibFile object.
    :param abbreviations: the list of abbreviations to extend, if empty extend all Strings.
    :return: output BibFile object.
    """
    strings_to_extend = {x.abbreviation: x.long_form for x in bib_file.get_strings()
                         if not abbreviations or x.abbreviation in abbreviations}
    for entry in bib_file.content:
        if isinstance(entry, Reference):
            fields = entry.get_fields()
            for field_type, data in fields.items():
                if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
                    continue
                if data in strings_to_extend:
                    fields[field_type] = "{" + strings_to_extend[data] + "}"
                elif "#" in data:
                    data_list = data.split("#")
                    final_data = ""
                    # Loop over all elements except the last one (to add the #s back)
                    for string in data_list[:-1]:
                        stripped = string.strip()
                        if stripped in strings_to_extend:
                            final_data += "{" + strings_to_extend[stripped] + "} # "
                        else:
                            final_data += stripped + " # "

                    # Add the final part of the string.
                    stripped = data_list[-1].strip()
                    if stripped in strings_to_extend:
                        final_data += "{" + strings_to_extend[stripped] + "}"
                    else:
                        final_data += stripped

                    fields[field_type] = final_data

    # Remove the strings (what an abomination).
    bib_file.content = [x for x in bib_file.content if
                        not isinstance(x, String) or (abbreviations and x.abbreviation not in abbreviations)]

    return bib_file


# JUST FOR TESTING
if __name__ == "__main__":
    test_file = file_parser.parse_bib("../biblatex-examples.bib", True)
    batch_extend_strings(test_file, ["pup"])
    batch_rename_abbreviation(test_file, "cup", "camup")
    file_generator.generate_bib(test_file, "extended-examples.bib", 15)
