def generate_bib(file_name, references, align_fields_position):
    with open(file_name, "w") as file:
        reference_string = ""
        for (ref_type, key), fields in references.items():
            if ref_type == "string":
                string_start = "@" + ref_type + "{" + key
                position_minus_length = align_fields_position - len(string_start)
                padding_size = position_minus_length if position_minus_length > 0 else 0
                reference_string +=  string_start + " " * padding_size + "= {" + fields + "}}"
            else:
                reference_string += "\n@" + ref_type + "{" + key + ",\n"
                for field_type, data in fields.items():
                    field_start = "  " + field_type
                    position_minus_length = align_fields_position - len(field_start)
                    padding_size = position_minus_length if position_minus_length > 0 else 0
                    reference_string += field_start + " " * padding_size + "= " + data + ",\n"
                reference_string += "}"
            reference_string += "\n"

        file.write(reference_string)
