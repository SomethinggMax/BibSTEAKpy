from objects import File, Reference
import utils.file_parser as file_parser
import utils.file_generator as file_generator

# Note for me: Account for the fact that all Reference objects
# should have the field on which you want to sort - Handle this exception!

def order_by_field(file: File, field: str, descending=False):
    """ 
    It acts on the same file and it sorts the Reference objects in the file
    based on a passed <field> argument in descending or ascending order
    """
    references = file.references
    sorted_by_year = sorted(references, key=lambda ref: getattr(ref, field), reverse=descending)
    file.references = sorted_by_year
    
    
# JUST FOR TESTING       
if __name__ == "__main__":
    test_file = file_parser.parse_bib("bibtests.bib", True)
    order_by_field(test_file, "author")
    print(test_file.references)
    