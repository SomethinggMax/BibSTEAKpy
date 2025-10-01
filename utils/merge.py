from objects import BibFile, Reference


def merge_reference(reference_1: Reference, reference_2: Reference) -> Reference:
    merged_reference = Reference(reference_1.comment_above_reference, reference_1.entry_type, reference_1.cite_key)
    reference_1_fields = reference_1.get_fields()
    reference_2_fields = reference_2.get_fields()

    for field_type, data in reference_1_fields.items():
        if field_type in reference_2_fields:
            if data != reference_2_fields[field_type]:
                print("Duplicate fields do not have the same contents!")
        setattr(merged_reference, field_type, data)  # add field from reference 1 to merged reference

    for field_type, data in reference_2_fields.items():
        if field_type not in merged_reference.get_fields():
            setattr(merged_reference, field_type, data)  # add field from reference 2 to merged reference

    return merged_reference


def merge_files(bib_file_1: BibFile, bib_file_2: BibFile) -> BibFile:
    # File name will be set when generating the file, this is just temporary.
    merged_bib_file = BibFile(bib_file_1.file_name + "+" + bib_file_2.file_name)

    # Add all strings first.
    merged_bib_file.content = bib_file_1.get_strings()
    merged_bib_file.content.extend(bib_file_2.get_strings())

    # Add references from bib file 1.
    for entry in bib_file_1.content:
        if type(entry) is Reference:
            if entry.cite_key in bib_file_2.get_cite_keys():
                merged_reference = merge_reference(entry, bib_file_2.get_reference(entry.cite_key))
                merged_bib_file.content.append(merged_reference)
            else:
                merged_bib_file.content.append(entry)

    # Add remaining references from bib file 2.
    for entry in bib_file_2.content:
        if type(entry) is Reference:
            if entry.cite_key not in merged_bib_file.get_cite_keys():
                merged_bib_file.content.append(entry)

    return merged_bib_file
