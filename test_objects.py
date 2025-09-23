import file_generator
import file_parser

bib_examples_original = "biblatex-examples.bib"
bib_examples_generated = "biblatex-examples-generated.bib"
bib_tests = "bibtests.bib"

example_file = file_parser.parse_bib(bib_examples_original, True)
# You can access Reference objects this way:
reference_objects = example_file.references
file_generator.generate_bib(bib_examples_generated, 15, example_file)

test_file = file_parser.parse_bib(bib_tests, True)
file_generator.generate_bib(bib_examples_generated, 15, test_file)