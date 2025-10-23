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


def cleanup(bib_file: BibFile):
    config = json_loader.load_config()

    # Load values from config (or default values).
    url = config.get("use_url", True)
    doi = config.get("use_doi", True)
    comments = config.get("comments", True)
    comment_entries = config.get("comment_entries", True)
    lowercase_entry_types = config.get("lowercase_entry_types", False)
    lowercase_fields = config.get("lowercase_fields", False)

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

    return bib_file
