import pprint
import difflib
import file_generator
import file_parser

bib_examples_original = "biblatex-examples.bib"
bib_examples_generated = "biblatex-examples-generated.bib"
bib_tests = "bibtests.bib"


result = file_parser.parse_bib(bib_examples_original, False)
test = file_parser.parse_bib(bib_tests, True)

pprint.pprint(result)
print(test)

# Some examples on how to access information from the dictionary.
# print(result[("book", "augustine")]["author"])
# print(result[("book", "cicero")]["annotation"])

# Generate file from the dictionary:
file_generator.generate_bib(bib_examples_generated, result, 15)

# Print the differences between the original file and the generated file:
with open(bib_examples_original) as original:
    original_string = original.readlines()
with open(bib_examples_generated) as generated:
    generated_string = generated.readlines()
for line in difflib.unified_diff(
        original_string, generated_string,
        fromfile=bib_examples_original, tofile=bib_examples_generated,
        lineterm=''):
    print(line)
