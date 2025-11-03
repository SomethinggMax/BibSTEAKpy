from objects import BibFile, Reference
import utils.file_parser as file_parser


# Note for me: Account for the fact that all Reference objects
# should have the field on which you want to sort - Handle this exception!
#TODO: BRO IT DONT WORK

def order_by_field(file: BibFile, field: str, descending=False):
    """ 
    It acts on the same file and it sorts the Reference objects in the file
    based on a passed <field> argument in descending or ascending order
    """

    references = file.get_references()
    sorted_by_year = sorted(references, key=lambda ref: getattr(ref, field), reverse=descending)
    file.content = sorted_by_year


# JUST FOR TESTING       
if __name__ == "__main__":
    test_file = file_parser.parse_bib("../bib_files/bibtests.bib")
    order_by_field(test_file, "author")
    print(test_file.references)
