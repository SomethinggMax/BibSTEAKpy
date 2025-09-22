import pprint
import difflib
import abbreviations_exec
import file_generator
import file_parser

bib_examples_original = "biblatex-examples.bib"
bib_examples_generated = "biblatex-examples-generated.bib"
bib_examples_edited = "biblatex-examples-edited.bib"
bib_tests = "bibtests.bib"


examples = file_parser.parse_bib(bib_examples_original, False)
test = file_parser.parse_bib(bib_tests, True)

# pprint.pprint(examples)
# print(test)

# Some examples on how to access information from the dictionary.
print(examples[("book", "augustine")]["author"])
print(examples[("book", "cicero")]["annotation"])

# Generate file from the dictionary:
file_generator.generate_bib(bib_examples_generated, examples, 15)

# Print the differences between the original file and the generated file:
# with open(bib_examples_original) as original:
#     original_string = original.readlines()
# with open(bib_examples_generated) as generated:
#     generated_string = generated.readlines()
# for line in difflib.unified_diff(
#         original_string, generated_string,
#         fromfile=bib_examples_original, tofile=bib_examples_generated,
#         lineterm=''):
#     print(line)

# examples_edited = batch_editor.batch_replace(
#     examples, ["publisher"],
#     "pup", "Princeton University Press")
# file_generator.generate_bib(bib_examples_edited, examples_edited, 15)
# with open(bib_examples_edited) as edited:
#     edited_string = edited.readlines()
# for line in difflib.unified_diff(
#         generated_string, edited_string,
#         fromfile=bib_examples_generated, tofile=bib_examples_edited,
#         lineterm=''):
#     print(line)

