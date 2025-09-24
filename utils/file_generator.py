
from objects import File, Reference

"""
You're old implementation - Now it will be used as a helpter function by generate_bib()
"""
def generate_bib_helper(file_name, references, align_fields_position):
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
        

def generate_bib(file_name, file: File, align_fields_position):
    references = {}
    for reference_obj in file.references:
        key = reference_obj.get_key()
        attribute_maps = reference_obj.get_non_none_fields()
        del attribute_maps["entry_type"]
        del attribute_maps["citekey"] # I should find a better way to handle this - I want to take only the fild values of the object
        references[key] = attribute_maps
    
    generate_bib_helper(file_name, references, align_fields_position)
    
    