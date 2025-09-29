from objects import BibFile, Reference, Comment, String


def generate_bib(bib_file: BibFile, file_name, align_fields_position):
    with open(file_name, "w") as file:
        reference_string = ""

        for entry in bib_file.content:
            match entry:
                case Comment():
                    reference_string += "\n" + entry.comment
                case String():
                    string_start = "@string{" + entry.abbreviation
                    position_minus_length = align_fields_position - len(string_start)
                    padding_size = position_minus_length if position_minus_length > 0 else 0
                    reference_string += string_start + " " * padding_size + "= {" + entry.long_form + "}}\n"
                case Reference():
                    reference_string += "\n@" + entry.entry_type + "{" + entry.citekey + ",\n"
                    attribute_maps = entry.get_non_none_fields()
                    del attribute_maps["entry_type"]
                    del attribute_maps["citekey"]  # I should find a better way to handle this - I want to take only the fild values of the object
                    for field_type, data in attribute_maps.items():
                        field_start = "  " + field_type
                        position_minus_length = align_fields_position - len(field_start)
                        padding_size = position_minus_length if position_minus_length > 0 else 0
                        reference_string += field_start + " " * padding_size + "= " + data + ",\n"
                    reference_string += "}\n"

        file.write(reference_string)
