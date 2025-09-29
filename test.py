import pprint
import difflib
import utils.abbreviations_exec as abbreviations_exec
import utils.file_generator as file_generator
import utils.file_parser as file_parser

bib_examples_original = "biblatex-examples.bib"
bib_examples_generated = "biblatex-examples-generated.bib"
bib_examples_edited = "biblatex-examples-edited.bib"
bib_tests = "bibtests.bib"

examples = file_parser.parse_bib(bib_examples_original, False)
test = file_parser.parse_bib(bib_tests, True)

# Some examples on how to access information from the dictionary.
# print(result[("book", "augustine")]["author"])
# print(result[("book", "cicero")]["annotation"])

# Generate file from the dictionary:
file_generator.generate_bib(examples, bib_examples_generated, 15)


# Print the differences between two files.:
def print_differences(from_file, to_file):
    with open(from_file) as first:
        first_string = first.readlines()
    with open(to_file) as second:
        second_string = second.readlines()
    for line in difflib.unified_diff(
            first_string, second_string,
            fromfile=from_file, tofile=to_file,
            lineterm=''):
        print(line)


print_differences(bib_examples_original, bib_examples_generated)

examples_edited = abbreviations_exec.execute_abbreviations(examples, False, 1000)
file_generator.generate_bib(examples_edited, bib_examples_edited, 15)

print_differences(bib_examples_generated, bib_examples_edited)
