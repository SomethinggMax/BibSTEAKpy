from copy import copy
from objects import BibFile, Reference, String, Comment
from utils import json_loader


def clean_url_and_doi(reference: Reference, use_url, use_doi) -> Reference:
    fields = reference.get_fields()
    url_field = fields.get("url")
    doi_field = fields.get("doi")

    # Delete both if url and doi are false.
    if not use_url and not use_doi:
        if url_field:
            delattr(reference, "url")
        if doi_field:
            delattr(reference, "doi")
    # Else only delete when both fields exist.
    elif url_field and doi_field:
        if not use_url:
            delattr(reference, "url")
        if not use_doi:
            delattr(reference, "doi")
    return reference


def remove_fields(reference: Reference, fields: [str]) -> Reference:
    for field in fields:
        if field in reference.get_fields():
            delattr(reference, field)
    return reference


def remove_comments(bib_file: BibFile):
    for entry in bib_file.content:
        if isinstance(entry, Reference):
            entry.comment_above_reference = ""
        elif isinstance(entry, String):
            entry.comment_above_string = ""
        elif isinstance(entry, str):
            bib_file.content.remove(entry)


def remove_comment_entries(bib_file: BibFile):
    for entry in bib_file.content:
        if isinstance(entry, Comment):
            bib_file.content.remove(entry)


def lower_entry_type(reference: Reference):
    reference.entry_type = reference.entry_type.lower()


def lower_fields(reference: Reference):
    for field_type, data in copy(reference).get_fields().items():
        delattr(reference, field_type)
        setattr(reference, field_type.lower(), data)


def change_field_enclosure(reference: Reference, start_enclosure: str, end_enclosure: str):
    for field_type, data in reference.get_fields().items():
        if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
            continue
        if not data.startswith('"') and not data.startswith('{'):
            continue
        if ' # ' in data:
            continue
        new_data = remove_enclosure(data)
        if not new_data.isdigit():
            new_data = start_enclosure + new_data + end_enclosure
        if data != new_data and (new_data.startswith('"{') and new_data.endswith('}"')):
            print(f"Old: {data}, new: {new_data}")
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
                print(f"Invalid braces for field value: '{field_value}', returning original value.")
                return field_value  # Give up on changing anything and just return the original value.
            result = "{" + result + "}"  # Add a pair of braces and hope it fixes the problem.
        else:
            break
    return result


def cleanup(bib_file: BibFile):
    config = json_loader.load_config()

    # Load values from config (or default values).
    url = config.get("use_url", True)
    doi = config.get("use_doi", True)
    comments = config.get("comments", True)
    comment_entries = config.get("comment_entries", True)
    lowercase_entry_types = config.get("lowercase_entry_types", False)
    lowercase_fields = config.get("lowercase_fields", False)
    braces_enclosure = config.get("braces_enclosure", False)
    quotation_marks_enclosure = config.get("quotation_marks_enclosure", False)

    fields = config.get("unnecessary_fields", [])

    if not comments:
        remove_comments(bib_file)
    if not comment_entries:
        remove_comment_entries(bib_file)

    for entry in bib_file.content:
        if isinstance(entry, Reference):
            remove_fields(entry, fields)
            clean_url_and_doi(entry, url, doi)
            if lowercase_entry_types:
                lower_entry_type(entry)
            if lowercase_fields:
                lower_fields(entry)
            if braces_enclosure and quotation_marks_enclosure:
                raise ValueError("Config file has invalid enclosures set, set only one to true.")
            if braces_enclosure:
                change_field_enclosure(entry, '{', '}')
            if quotation_marks_enclosure:
                change_field_enclosure(entry, '"', '"')

    return bib_file
