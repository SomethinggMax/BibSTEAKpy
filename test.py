import pprint
import difflib
import batch_editor
import file_generator
import file_parser
import GroupByRefType

bib_examples_original = "testfiles/biblatex-examples.bib"
bib_examples_generated = "testfiles/biblatex-examples-generated.bib"
bib_examples_edited = "testfiles/biblatex-examples-edited.bib"
bib_examples_grouped = "testfiles/biblatex-examples-grouped.bib"
bib_tests = "testfiles/bibtests.bib"

#Create 2 dictonaries, examples from "bib_examples_original" and test from "bib_tests"
examples = file_parser.parse_bib(bib_examples_original, False)
test = file_parser.parse_bib(bib_tests, True)

# pprint.pprint(examples)
# print(test)

# Some examples on how to access information from the dictionary.
# print(result[("book", "augustine")]["author"])
# print(result[("book", "cicero")]["annotation"])

# Generate file from the dictionary:
# file_generator.generate_bib(bib_examples_generated, examples, 15)

groupedExamples = GroupByRefType.groupByRefType(examples, GroupByRefType.GroupingType.ATOZ)

file_generator.generate_bib(bib_examples_grouped, groupedExamples, 15)

# # Print the differences between the original file and the generated file:
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

