import difflib
import os
import re
import utils.file_generator as file_generator
import utils.file_parser as file_parser
from CLI import get_bib_file_names
from utils import batch_editor, sub_bib, merge, cleanup, ordering, json_loader


def file_to_string(file_name):
    with open(file_name, encoding='utf-8') as file:
        return file.readlines()


def convert_to_utf8(old_path, new_path, encoding):
    with open(old_path, encoding=encoding) as file:
        content = file.readlines()
    with open(new_path, 'w', encoding="utf-8") as file:
        file.writelines(content)
    print(f"Converted file {old_path} to utf8.")


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
            bib_file = file_parser.parse_bib(path)
        except UnicodeDecodeError:
            try:
                convert_to_utf8(path, path, 'windows-1252')
                bib_file = file_parser.parse_bib(path)
            except Exception as e:
                print(f"Skipping file {file_name}, it cannot be decoded with UTF-8 or windows-1252. {e}")
                continue
        except ValueError as e:
            print(f"Skipping file {file_name}, it cannot be correctly parsed: {e}")
            continue
        file_generator.generate_bib(bib_file, temp_file_name)

        if is_different(path, temp_file_name, True, True, True):
            print(f"Difference between original and generated file: {path}")
            print_differences(path, temp_file_name)
            return False

        # Check if the contents are the same when the generated file is parsed again:
        assert file_parser.parse_bib(temp_file_name).content == bib_file.content
    if os.path.isfile(temp_file_name):
        os.remove(temp_file_name)
    return True


if __name__ == '__main__':
    if not os.listdir(json_loader.get_wd_path()):
        print("The working directory is empty!")
    elif test_files(json_loader.get_wd_path()):
        print("All files in the working directory seem correctly parsed and generated.")
