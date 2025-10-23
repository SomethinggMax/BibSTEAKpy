import json
from objects import BibFile, Reference, String, Comment


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


def cleanup(bib_file: BibFile):
    with open("config.json") as config:
        data = json.load(config)

    # Default values.
    url = True
    doi = True
    comments = True
    comment_entries = True

    fields = []

    # Load values from config.
    for key, value in data.items():
        if key == "use_url":
            url = value
        elif key == "use_doi":
            doi = value
        elif key == "comments":
            comments = value
        elif key == "comment_entries":
            comment_entries = value
        elif key == "unnecessary_fields":
            fields = value

    if not comments:
        remove_comments(bib_file)
    if not comment_entries:
        remove_comment_entries(bib_file)

    for entry in bib_file.content:
        if isinstance(entry, Reference):
            remove_fields(entry, fields)
            clean_url_and_doi(entry, url, doi)

    return bib_file
