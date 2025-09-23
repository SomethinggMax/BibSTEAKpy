from objects import File, Reference
import file_parser
import file_generator

# Account for the fact that all Reference objects should have the field on which you want to sort on in the future

def order_by_field(file: File, field: str, descending=False):
    references = file.references
    sorted_by_year = sorted(references, key=lambda ref: getattr(ref, field), reverse=descending)
    file.references = sorted_by_year
    
    
    
    
    
    
if __name__ == "__main__":
    test_file = file_parser.parse_bib("bibtests.bib", True)
    order_by_field(test_file, "author")
    print(test_file.references)
    