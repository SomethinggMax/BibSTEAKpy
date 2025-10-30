from objects import BibFile, Reference, String
from utils import file_parser, file_generator


def batch_replace(bib_file: BibFile, fields_to_edit: list[str], old_string: str, new_string: str) -> BibFile:
    """
    Searches the references for occurrences of the old_string and replaces them with the new_string.
    Only searches the fields given in the fields_to_edit parameter, or all if empty.
    Also replaces the long_form of string definitions, does not replace string abbreviations.
    """
    for entry in bib_file.content:
        #keep strings
        if type(entry) is String:
            entry.long_form = entry.long_form.replace(old_string, new_string)


        if type(entry) is Reference:
            fields = entry.get_fields()
            for field_type, data in fields.items():
                #simply keep comments, entry types and citekeys
                if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
                    continue
                #we either look through all fields OR if the specific field type is found we also go ahead
                if fields_to_edit == [] or field_type in fields_to_edit:
                    if "#" not in data:
                        if "\"" in data or "{" in data:
                            fields[field_type] = data.replace(old_string, new_string)
                    else:
                        data_list = data.split(" # ")
                        final_data = ""
                        # Loop over all elements except the last one (to add the #s back)
                        for string in data_list[:-1]:
                            stripped = string.strip()
                            if "\"" in stripped or "{" in stripped:
                                final_data += stripped.replace(old_string, new_string) + " # "
                            else:
                                final_data += stripped + " # "

                        # Add the final part of the string.
                        stripped = data_list[-1].strip()
                        if "\"" in stripped or "{" in stripped:
                            final_data += stripped.replace(old_string, new_string)
                        else:
                            final_data += stripped

                        fields[field_type] = final_data
    return bib_file


def batch_rename_abbreviation(bib_file: BibFile, old_abbreviation: str, new_abbreviation: str) -> BibFile:
    """
    Rename a String abbreviation in the BibFile.
    """
    for entry in bib_file.content:
        if isinstance(entry, String):
            if entry.abbreviation == old_abbreviation:
                entry.abbreviation = new_abbreviation
            elif entry.abbreviation == new_abbreviation:
                raise ValueError(f"Abbreviation '{new_abbreviation}' already exists in the bib file!")
        if isinstance(entry, Reference):
            fields = entry.get_fields()
            for field_type, data in fields.items():
                if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
                    continue
                if data == old_abbreviation:
                    fields[field_type] = new_abbreviation
                elif " # " in data:
                    data_list = data.split(" # ")
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


def batch_shorten_string(bib_file: BibFile, fields_to_edit: list[str], string: String) -> BibFile:
    """
    Shortens all occurrences of the string long form and adds the String to the file if new.
    :param bib_file: input BibFile object.
    :param fields_to_edit: the fields to check for occurrences of the long form.
    :param string: the String to shorten.
    :return: output BibFile object.
    """
    existing_string_dict = {x.abbreviation: x.long_form for x in bib_file.get_strings()}
    if string.abbreviation not in existing_string_dict:
        bib_file.content.insert(0, string)
    elif string.long_form != existing_string_dict[string.abbreviation]:
        raise ValueError("Abbreviation is already in use with a different long form!")

    for entry in bib_file.content:
        if isinstance(entry, Reference):
            fields = entry.get_fields()
            for field_type, data in fields.items():
                if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
                    continue
                if not fields_to_edit or field_type in fields_to_edit:
                    number_of_occurrences = data.count(string.long_form)
                    if number_of_occurrences == 0:
                        continue

                    def replace_string_and_return_count(old_string: str, new_string: str) -> int:
                        updated_data = fields[field_type]
                        count = updated_data.count(old_string)
                        fields[field_type] = updated_data.replace(old_string, new_string)
                        return count

                    if data == "{" + string.long_form + "}" or data == "\"" + string.long_form + "\"":
                        fields[field_type] = string.abbreviation
                        number_of_occurrences -= 1
                    else:
                        number_of_occurrences -= replace_string_and_return_count(
                            "{" + string.long_form + "}", "# " + string.abbreviation + " #")
                        number_of_occurrences -= replace_string_and_return_count(
                            "\"" + string.long_form + "\"", "# " + string.abbreviation + " #")
                        number_of_occurrences -= replace_string_and_return_count(
                            "{" + string.long_form, "# " + string.abbreviation + " {")
                        number_of_occurrences -= replace_string_and_return_count(
                            "\"" + string.long_form, "# " + string.abbreviation + " \"")
                        number_of_occurrences -= replace_string_and_return_count(
                            string.long_form + "}", "} # " + string.abbreviation)
                        number_of_occurrences -= replace_string_and_return_count(
                            string.long_form + "\"", "\" # " + string.abbreviation)
                        if number_of_occurrences != 0:
                            first_char = data[0]
                            if first_char == "{":
                                number_of_occurrences -= replace_string_and_return_count(
                                    string.long_form, "} # " + string.abbreviation + " # {")
                            elif first_char == "\"":
                                number_of_occurrences -= replace_string_and_return_count(
                                    string.long_form, "\" # " + string.abbreviation + " # \"")
                            else:
                                raise ValueError("Could not determine type of enclosure for field.")
                    if number_of_occurrences != 0:
                        raise ValueError("Could not find all occurrences of the long form! (probably a bug...)")
    return bib_file


def batch_extend_strings(bib_file: BibFile, abbreviations: list[str]) -> BibFile:
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
                elif " # " in data:
                    data_list = data.split(" # ")
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
    test_file = file_parser.parse_bib("../bib_files/biblatex-examples.bib")
    batch_extend_strings(test_file, ["pup"])
    batch_shorten_string(test_file, [], String("", "SF", "Science Fiction"))
    batch_rename_abbreviation(test_file, "cup", "camup")
    file_generator.generate_bib(test_file, "../bib_files/extended-examples.bib")
