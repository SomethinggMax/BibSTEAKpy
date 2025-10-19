import difflib
import os
import re
import utils.file_generator as file_generator
import utils.file_parser as file_parser
from CLI import get_bib_file_names, get_working_directory_path
from utils import batch_editor, sub_bib, merge, cleanup
from utils.Reftype import sortByReftype, GroupingType
from utils.filtering import search


def file_to_string(file_name):
    with open(file_name, encoding='utf-8') as file:
        return file.readlines()


def convert_to_utf8(old_path, new_path, encoding):
    with open(old_path, encoding=encoding) as file:
        content = file.readlines()
    with open(new_path, 'w', encoding="utf-8") as file:
        file.writelines(content)


def print_differences(from_file, to_file):
    """
    Print the differences between the two files.
    """
    first_string = file_to_string(from_file)
    second_string = file_to_string(to_file)
    for line in difflib.unified_diff(
            first_string, second_string,
            fromfile=from_file, tofile=to_file,
            lineterm=''):
        print(line)


def is_different(from_file, to_file, ignore_spaces, ignore_commas, ignore_capitalization) -> bool:
    """
    Check if two files contain any differences (ignoring newlines).
    :param from_file:
    :param to_file:
    :param ignore_spaces: if True ignore any differences in spaces.
    :param ignore_commas: if True ignore any differences in commas (since in the last field the comma is not necessary)
    :param ignore_capitalization: if True ignore any difference in capitalization.
    :return:
    """
    first_string_list = file_to_string(from_file)
    second_string_list = file_to_string(to_file)
    new_first_string = ""
    new_second_string = ""
    for string in first_string_list:
        new_first_string += string
    for string in second_string_list:
        new_second_string += string
    if ignore_spaces:
        new_first_string = re.sub(r'\s+', '', new_first_string)
        new_second_string = re.sub(r'\s+', '', new_second_string)
    if ignore_commas:
        new_first_string = re.sub(r',', '', new_first_string)
        new_second_string = re.sub(r',', '', new_second_string)
    if ignore_capitalization:
        new_first_string = new_first_string.lower()
        new_second_string = new_second_string.lower()
    differences = difflib.unified_diff(new_first_string, new_second_string)
    if any(True for _ in differences):
        return True
    return False


def test_files(directory_path) -> bool:
    """
    Check if all the bib files in the directory are correctly parsed and generated.
    Works by checking differences between original and generated file. Ignores spaces.
    :param directory_path:
    :return: if the files are correctly parsed and generated.
    """
    if not os.listdir(directory_path):
        print("The directory is empty!")
        return True

    file_names = get_bib_file_names(directory_path)
    temp_file_name = "new-generated-temporary-test-file.bib"

    for file_name, index in file_names:
        print(f"Testing parsing and generation of file '{file_name}'")
        path = os.path.join(directory_path, file_name)
        try:
            bib_file = file_parser.parse_bib(path, False)
        except UnicodeDecodeError:
            try:
                convert_to_utf8(path, path, 'windows-1252')
                bib_file = file_parser.parse_bib(path, False)
            except Exception as e:
                print(f"Skipping file {file_name}, it cannot be decoded with UTF-8 or windows-1252. {e}")
                continue
        except ValueError as e:
            print(f"Skipping file {file_name}, it cannot be correctly parsed: {e}")
            continue
        file_generator.generate_bib(bib_file, temp_file_name, 15)
        if is_different(path, temp_file_name, True, True, True):
            print(f"Difference between original and generated file: {path}")
            print_differences(path, temp_file_name)
            return False
    if os.path.isfile(temp_file_name):
        os.remove(temp_file_name)
    return True


if __name__ == '__main__':
    bib_examples_original = "bib_files/biblatex-examples.bib"
    bib_examples_generated = "bib_files/biblatex-examples-generated.bib"
    bib_examples_edited = "bib_files/biblatex-examples-edited.bib"
    articles_examples = "bib_files/articles-examples.bib"
    bib_tests = "bib_files/bibtests.bib"
    bib_merge_test = "bib_files/bib-merge-test.bib"
    merge_result = "bib_files/merge-result.bib"

    examples = file_parser.parse_bib(bib_examples_original, False)
    test = file_parser.parse_bib(bib_tests, True)
    merge_test = file_parser.parse_bib(bib_merge_test, True)

    # Generate file from the dictionary:
    file_generator.generate_bib(examples, bib_examples_generated, 15)

    if not os.listdir(get_working_directory_path()):
        print("The working directory is empty!")
    elif test_files(get_working_directory_path()):
        print("All files in the working directory seem correctly parsed and generated.")

    print_differences(bib_examples_original, bib_examples_generated)

    # test filtering/searching
    displayfile = search(examples, "english")
    file_generator.generate_bib(displayfile, "bib_files/newfile.bib", 15)

    batch_editor.batch_replace(examples, [], "pup", "Princeton University Press")
    cleanup.cleanup(examples)
    file_generator.generate_bib(examples, bib_examples_edited, 15)

    print_differences(bib_examples_generated, bib_examples_edited)

    articles = sub_bib.sub_bib_entry_types(test, ["article"])
    file_generator.generate_bib(articles, articles_examples, 15)

    file_generator.generate_bib(merge.merge_files(merge_test, test), merge_result, 15)

    tagged_sub_file = sub_bib.sub_bib_tags(examples, ["Computer Science", "Virtual memory and storage"])
    file_generator.generate_bib(tagged_sub_file, "bib_files/tagged-examples.bib", 15)

    # testing grouping
    sortByReftype(examples, GroupingType.ZTOA)
    file_generator.generate_bib(examples, "bib_files/bib-examples-grouped.bib", 15)
