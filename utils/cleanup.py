import json

from objects import BibFile, Reference


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


def cleanup(bib_file: BibFile):
    with open("config.json") as config:
        data = json.load(config)

    # Default values.
    url = True
    doi = True

    # Load values from config.
    for key, value in data.items():
        if key == "use_url":
            url = value
        elif key == "use_doi":
            doi = value

    for entry in bib_file.content:
        if isinstance(entry, Reference):
            clean_url_and_doi(entry, url, doi)

    return bib_file
