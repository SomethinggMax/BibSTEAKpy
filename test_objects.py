from utils import file_generator 
from utils import file_parser 

bib_examples_original_path = "bib_files/biblatex-examples.bib"
bib_examples_generated_path = "bib_files/biblatex-examples-generated.bib"
bib_tests_path = "bib_files/bibtests.bib"

example_file = file_parser.parse_bib(bib_examples_original_path, True)
test_file = file_parser.parse_bib(bib_tests_path, True)

reference_objects = example_file.references # You can access Reference objects this way:

file_generator.generate_bib(bib_examples_generated_path, test_file, 15)


