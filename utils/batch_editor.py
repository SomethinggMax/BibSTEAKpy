# Searches the references for occurrences of the old_string and replaces them with the new_string.
# Only searches the fields given in the fields_to_edit parameter, or all if empty.
from objects import BibFile, Reference


def batch_replace(bib_file, fields_to_edit, old_string, new_string) -> BibFile:
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
