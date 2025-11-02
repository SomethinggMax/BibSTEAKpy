import utils.batch_editor as batch_editor
from objects import String
from utils import json_loader, file_parser, file_generator


def execute_abbreviations(bib_file, minimize, max_abbreviations):
    data = json_loader.load_abbreviations()
    config = json_loader.load_config()
    add_abbreviations_as_strings = config.get("add_abbreviations_as_strings", False)

    # Minimize everything.
    for abbreviation, list in data.items():
        if add_abbreviations_as_strings:
            # First replace everything for the long_form, to ensure that shorten_string finds all occurrences.
            batch_editor.batch_replace(bib_file, list[1], abbreviation, list[0])

            batch_editor.batch_shorten_string(bib_file, list[1], String("", abbreviation, list[0]))
            batch_editor.replace_string(bib_file, list[0], abbreviation)
        else:
            batch_editor.batch_replace(bib_file, list[1], list[0], abbreviation)

    if minimize:
        # Expand everything after counter + 1 > max_abbreviations.
        for counter, (abbreviation, list) in enumerate(data.items()):
            if counter + 1 > max_abbreviations:
                if add_abbreviations_as_strings:
                    batch_editor.replace_string(bib_file, abbreviation, list[0])
                else:
                    batch_editor.batch_replace(bib_file, list[1], abbreviation, list[0])
    else:
        # Expand everything before counter + 1 > max_abbreviations.
        for counter, (abbreviation, list) in enumerate(data.items()):
            if counter + 1 < max_abbreviations:
                if add_abbreviations_as_strings:
                    batch_editor.replace_string(bib_file, abbreviation, list[0])
                else:
                    batch_editor.batch_replace(bib_file, list[1], abbreviation, list[0])
    return bib_file


if __name__ == '__main__':
    examples = file_parser.parse_bib("../bib_files/biblatex-examples.bib")
    execute_abbreviations(examples, True, 1000)
    file_generator.generate_bib(examples, "../bib_files/minimized_examples.bib")

    minimized = file_parser.parse_bib("../bib_files/minimized_examples.bib")
    assert minimized.content == examples.content

    execute_abbreviations(examples, True, 1000)
    assert minimized.content == examples.content

    execute_abbreviations(minimized, False, 1000)
    execute_abbreviations(examples, False, 1000)
    assert minimized.content == examples.content

    file_generator.generate_bib(minimized, "../bib_files/maximized_examples.bib")
