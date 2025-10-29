from objects import BibFile, Reference, Comment, String, Preamble, Enclosure
from utils import json_loader

MAXIMUM_FIELD_LENGTH = 100


def get_maximum_alignment(bib_file: BibFile) -> int:
    """
    Gets the alignment position based on the longest length of string abbreviations and field_types.
    :param bib_file:
    :return:
    """
    maximum = 0
    for entry in bib_file.content:
        if isinstance(entry, String):
            maximum = max(maximum, len(entry.abbreviation) + 9)  # len(@string{)=8 +1 for a space after the abbreviation
        elif isinstance(entry, Reference):
            for field_type, data in entry.get_fields().items():
                if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
                    continue
                maximum = max(maximum, len(field_type) + 3)  # two spaces before field_type, 1 space after
    return maximum


def generate_field(field_type: str, align_fields_position: int, data: str, add_newlines: bool) -> str:
    """
    Generates a str of a field based on parameters.
    """
    field_start = "  " + field_type
    position_minus_length = align_fields_position - len(field_start)
    padding_size = position_minus_length if position_minus_length > 0 else 0
    field = field_start + " " * padding_size + "= " + data + ",\n"
    if add_newlines:
        counter = 0
        last_word = ""
        new_field = ""
        for char in field:
            if char == " ":
                if counter >= MAXIMUM_FIELD_LENGTH:
                    padding = " " * (align_fields_position + 1)
                    new_field += "\n" + padding + last_word
                    counter = len(padding + last_word)
                else:
                    new_field += last_word
                last_word = ""
            last_word += char
            counter += 1
        field = new_field + last_word
    return field


def generate_bib(bib_file: BibFile, file_path, align_fields_position=None, add_newlines_in_fields=None):
    """
    Generates a bib file from the BibFile object at the file_path (overwrites if the path already exists).
    :param bib_file: the BibFile object.
    :param file_path: the path to generate the file at.
    :param align_fields_position: the position to align the '=' at. If None: calculated based on entries.
    :param add_newlines_in_fields: add newlines to fields if they are longer than MAXIMUM_FIELD_LENGTH characters.
    :return:
    """
    if align_fields_position is None:
        align_fields_position = get_maximum_alignment(bib_file)
    if add_newlines_in_fields is None:
        add_newlines_in_fields = json_loader.load_config().get("remove_newlines_in_fields", False)

    with open(file_path, "w", encoding="utf-8") as file:
        final_string = ""

        for entry in bib_file.content:
            match entry:
                case Comment():
                    final_string += "@comment{" + entry.comment + "}\n"
                case Preamble():
                    final_string += "@preamble{" + entry.preamble + "}\n"
                case String():
                    if entry.comment_above_string != "":
                        final_string += entry.comment_above_string + "\n"
                    string_start = "@string{" + entry.abbreviation
                    position_minus_length = align_fields_position - len(string_start)
                    padding_size = position_minus_length if position_minus_length > 0 else 0
                    if entry.enclosure == Enclosure.BRACKETS:
                        final_string += string_start + " " * padding_size + "= {" + entry.long_form + "}}\n"
                    elif entry.enclosure == Enclosure.QUOTATION_MARKS:
                        final_string += string_start + " " * padding_size + "= \"" + entry.long_form + "\"}\n"
                case Reference():
                    if entry.comment_above_reference != "":
                        final_string += "\n"
                    final_string += entry.comment_above_reference + "\n@" + entry.entry_type + "{" + entry.cite_key + ",\n"
                    for field_type, data in entry.get_fields().items():
                        if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
                            continue
                        final_string += generate_field(field_type, align_fields_position, data, add_newlines_in_fields)
                    final_string += "}\n"
                case _:
                    final_string += entry
        file.write(final_string)
