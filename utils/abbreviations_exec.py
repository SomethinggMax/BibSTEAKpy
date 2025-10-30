import utils.batch_editor as batch_editor
from utils import json_loader


def execute_abbreviations(bib_file, minimize, max_abbreviations):
    data = json_loader.load_abbreviations()

    for abbreviation, list in data.items():
        batch_editor.batch_replace(bib_file, list[1], list[0], abbreviation)

    if minimize:
        for counter, (abbreviation, list) in enumerate(data.items()):
            if counter + 1 > max_abbreviations:
                batch_editor.batch_replace(bib_file, list[1], abbreviation, list[0])
    else:
        for counter, (abbreviation, list) in enumerate(data.items()):
            if counter + 1 < max_abbreviations:
                batch_editor.batch_replace(bib_file, list[1], abbreviation, list[0])

    return bib_file
