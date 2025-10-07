import difflib
import re
import utils.file_generator as file_generator
import utils.file_parser as file_parser
from utils import batch_editor, sub_bib, merge, cleanup

bib_examples_original = "biblatex-examples.bib"
bib_examples_generated = "biblatex-examples-generated.bib"
bib_examples_edited = "biblatex-examples-edited.bib"
articles_examples = "articles-examples.bib"
bib_tests = "bibtests.bib"
bib_merge_test = "bib-merge-test.bib"
merge_result = "merge-result.bib"

examples = file_parser.parse_bib(bib_examples_original, False)
test = file_parser.parse_bib(bib_tests, True)
merge_test = file_parser.parse_bib(bib_merge_test, True)

# Some examples on how to access information from the dictionary.
# print(result[("book", "augustine")]["author"])
# print(result[("book", "cicero")]["annotation"])

# Generate file from the dictionary:
file_generator.generate_bib(examples, bib_examples_generated, 15)


def file_to_string(file_name):
    with open(file_name) as file:
        return file.readlines()


# Print the differences between two files.:
def print_differences(from_file, to_file):
    first_string = file_to_string(from_file)
    second_string = file_to_string(to_file)
    for line in difflib.unified_diff(
            first_string, second_string,
            fromfile=from_file, tofile=to_file,
            lineterm=''):
        print(line)


def is_different(from_file, to_file, ignore_spaces) -> bool:
    """
    Check if two files contain any differences.
    :param from_file:
    :param to_file:
    :param ignore_spaces: if True ignore any differences in spaces.
    :return:
    """
    first_string_list = file_to_string(from_file)
    second_string_list = file_to_string(to_file)
    new_first_string = ""
    new_second_string = ""
    if ignore_spaces:
        for string in first_string_list:
            new_first_string += re.sub(r'\s+', '', string)
        for string in second_string_list:
            new_second_string += re.sub(r'\s+', '', string)
        differences = difflib.unified_diff(new_first_string, new_second_string)
    else:
        differences = difflib.unified_diff(first_string_list, second_string_list)
    if any(True for _ in differences):
        return True
    return False


print(f"Different when ignoring spaces: {is_different(bib_examples_original, bib_examples_generated, True)}")
print_differences(bib_examples_original, bib_examples_generated)

batch_editor.batch_replace(examples, [], "pup", "Princeton University Press")
cleanup.cleanup(examples)
file_generator.generate_bib(examples, bib_examples_edited, 15)

print_differences(bib_examples_generated, bib_examples_edited)

articles = sub_bib.sub_bib_entry_types(test, ["article"])
file_generator.generate_bib(articles, articles_examples, 15)

file_generator.generate_bib(merge.merge_files(merge_test, test), merge_result, 15)

tagged_sub_file = sub_bib.sub_bib_tags(examples, ["Computer Science", "Virtual memory and storage"])
file_generator.generate_bib(tagged_sub_file, "tagged-examples.bib", 15)
