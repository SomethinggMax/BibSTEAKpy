from copy import copy
from objects import BibFile, Reference, String, Comment
from utils import json_loader, file_parser, file_generator


def _convert_symbols(reference: Reference):
    special_latex_to_unicode = {
        '{\\ss}': 'ß', '\\ss': 'ß',
        '{\\o}': 'ø', '\\o': 'ø',
        '{\\O}': 'Ø', '\\O': 'Ø',
        '{\\ae}': 'æ', '\\ae': 'æ',
        '{\\AE}': 'Æ', '\\AE': 'Æ',
        '{\\l}': 'ł', '\\l': 'ł',
        '{\\L}': 'Ł', '\\L': 'Ł'
    }
    latex_to_unicode = {
        "\\`": ('\u0300', ['a', 'e', 'i', 'o', 'u']),  # Grave accent
        "\\'": ('\u0301', ['a', 'e', 'i', 'o', 'u', 'y', 'c']),  # Acute accent
        "\\^": ('\u0302', ['a', 'e', 'i', 'o', 'u']),  # Circumflex accent
        "\\~": ('\u0303', ['a', 'n', 'o']),  # Tilde
        "\\=": ('\u0304', ['a', 'e', 'i', 'o', 'u', 'p']),  # Macron
        "\\u": ('\u0306', ['a', 'e', 'i', 'o', 'u']),  # Breve
        "\\.": ('\u0307', ['o']),  # Dot above
        '\\"': ('\u0308', ['a', 'e', 'i', 'o', 'u']),  # Diaeresis
        "\\a": ('\u030A', ['a']), "\\r": ('\u030A', ['a']),  # Ring above
        "\\H": ('\u030B', ['o', 'u']),  # Double acute accent
        "\\v": ('\u030C', ['c', 'r', 's', 'z']),  # Caron
        "\\c": ('\u0327', ['c', 's']),  # Cedilla
        "\\k": ('\u030C', ['a', 'e', 'i', 'o', 'u']),  # Ogonek
    }
    for field_type, data in reference.get_fields().items():
        if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
            continue
        for key, value in special_latex_to_unicode.items():
            data = data.replace(key, value)
        for latex_command, (combining_mark, letters) in latex_to_unicode.items():
            capitalized = [x.capitalize() for x in letters]
            for letter in letters + capitalized:
                data = data.replace('{' + latex_command + '{\\' + letter + '}}', letter + combining_mark)
                data = data.replace(latex_command + '{\\' + letter + '}', letter + combining_mark)
                data = data.replace('{' + latex_command + '{' + letter + '}}', letter + combining_mark)
                data = data.replace(latex_command + '{' + letter + '}', letter + combining_mark)
                data = data.replace('{' + latex_command + '\\' + letter + '}', letter + combining_mark)
                data = data.replace('{' + latex_command + letter + '}', letter + combining_mark)
                data = data.replace('{' + latex_command + ' ' + letter + '}', letter + combining_mark)
        setattr(reference, field_type, data)  # Actually update the field.


def _clean_url_if_doi(reference: Reference) -> Reference:
    fields = reference.get_fields()
    url_field = fields.get("url")
    doi_field = fields.get("doi")

    # Only delete when both fields exist.
    if url_field and doi_field:
        delattr(reference, "url")
    return reference


def _remove_fields(reference: Reference, fields: [str]) -> Reference:
    for field in fields:
        if field in reference.get_fields():
            delattr(reference, field)
    return reference


def _remove_comments(bib_file: BibFile):
    for entry in bib_file.content:
        if isinstance(entry, Reference):
            entry.comment_above_reference = ""
        elif isinstance(entry, String):
            entry.comment_above_string = ""
        elif isinstance(entry, str):
            bib_file.content.remove(entry)


def _remove_comment_entries(bib_file: BibFile):
    for entry in bib_file.content:
        if isinstance(entry, Comment):
            bib_file.content.remove(entry)


def _lower_entry_type(reference: Reference):
    reference.entry_type = reference.entry_type.lower()


def _lower_fields(reference: Reference):
    for field_type, data in copy(reference).get_fields().items():
        delattr(reference, field_type)
        setattr(reference, field_type.lower(), data)


def _order_field_names(reference: Reference, field_order: list[str]) -> Reference:
    def order_key(item: (str, str)):
        # Use order from field_order.
        # If field is not in field_order return the len(field_order).
        # This means that all other fields will have the same value, so the original order will be kept.
        return field_order.index(item[0]) if item[0] in field_order else len(field_order)

    fields = copy(reference).get_fields()
    # Remove internal/meta fields from ordering context.
    for k in ["comment_above_reference", "entry_type", "cite_key"]:
        if k in fields:
            fields.pop(k)
    sorted_fields = sorted(fields.items(), key=order_key)

    # Every field in sorted_fields will be removed and added in the sorted order.
    for field_type, data in sorted_fields:
        delattr(reference, field_type)
        setattr(reference, field_type, data)
    return reference


def _change_field_enclosure(reference: Reference, start_enclosure: str, end_enclosure: str):
    for field_type, data in reference.get_fields().items():
        if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
            continue
        if ' # ' in data:
            continue
        new_data = remove_enclosure(data)
        if new_data == data:
            continue
        if not new_data.isdigit():
            new_data = start_enclosure + new_data + end_enclosure
        setattr(reference, field_type, new_data)


def remove_enclosure(field_value: str) -> str:
    start_enclosure = ""
    end_enclosure = ""
    for char in field_value:
        if char == '{':
            start_enclosure += char
        elif char == '"':
            start_enclosure += char
        else:
            break
    for char in reversed(field_value):
        if char == '}':
            end_enclosure += '{'
        elif char == '"':
            end_enclosure += char
        else:
            break

    # Remove enclosure while start and end enclosure are equal.
    result = field_value
    for (start, end) in zip(start_enclosure, end_enclosure):
        if start == end:
            result = result[1:-1]
        else:
            break

    # Check if braces are still correct.
    for x in range(5):
        braces_level = 0
        for char in result:
            if char == '{':
                braces_level += 1
            elif char == '}':
                braces_level -= 1
            if braces_level < 0:
                break

        if braces_level != 0:
            if x > 3:
                return field_value  # Give up on changing anything and just return the original value.
            result = "{" + result + "}"  # Add a pair of braces and hope it fixes the problem.
        else:
            break
    return result


def cleanup(bib_file: BibFile):
    config = json_loader.load_config()

    # Load values from config (or default values).
    convert_special_symbols = config.get("convert_special_symbols_to_unicode", False)
    prefer_doi_over_url = config.get("prefer_doi_over_url", False)
    delete_comments = config.get("remove_comments", False)
    delete_comment_entries = config.get("remove_comment_entries", False)
    lowercase_entry_types = config.get("lowercase_entry_types", False)
    lowercase_fields = config.get("lowercase_fields", False)
    braces_enclosure = config.get("change_enclosures_to_braces", False)
    quotation_marks_enclosure = config.get("change_enclosures_to_quotation_marks", False)

    fields = config.get("unnecessary_fields", [])
    field_order = config.get("preferred_field_order", [])

    if delete_comments:
        _remove_comments(bib_file)
    if delete_comment_entries:
        _remove_comment_entries(bib_file)

    for entry in bib_file.content:
        if isinstance(entry, Reference):
            if lowercase_entry_types:
                _lower_entry_type(entry)
            if lowercase_fields:
                _lower_fields(entry)
            if prefer_doi_over_url:
                _clean_url_if_doi(entry)
            if braces_enclosure and quotation_marks_enclosure:
                raise ValueError("Config file has invalid enclosures set, set only one to true.")
            if convert_special_symbols:
                _convert_symbols(entry)
            if braces_enclosure:
                _change_field_enclosure(entry, '{', '}')
            if quotation_marks_enclosure:
                _change_field_enclosure(entry, '"', '"')

            _remove_fields(entry, fields)
            _order_field_names(entry, field_order)

    return bib_file


# JUST FOR TESTING
if __name__ == '__main__':
    test_file = file_parser.parse_bib("../bib_files/biblatex-examples.bib")
    cleanup(test_file)
    file_generator.generate_bib(test_file, "../bib_files/cleaned-examples.bib")
