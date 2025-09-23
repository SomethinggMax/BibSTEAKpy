# Searches the references for occurrences of the old_string and replaces them with the new_string.
# Only searches the fields given in the fields_to_edit parameter, or all if empty.
def batch_replace(references, fields_to_edit, old_string, new_string):
    for (ref_type, key), fields in references.items():
        if ref_type == "string":
            continue
        for field_type, data in fields.items():
            if not fields_to_edit:
                fields[field_type] = data.replace(old_string, new_string)
            elif field_type in fields_to_edit:
                fields[field_type] = data.replace(old_string, new_string)
    return references

