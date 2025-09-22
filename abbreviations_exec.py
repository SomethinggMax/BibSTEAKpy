import json
import pprint
import batch_editor
def execute_abbreviations(references, minimize, max_abbreviations):
    with open('abbreviations.json') as abbreviations_data:
        data = json.load(abbreviations_data)
        abbreviations_data.close()
        pprint.pprint(data)

    for abbreviation, list in data.items():
        references = batch_editor.batch_replace(references, list[1], abbreviation, list[0])

    if minimize:
        for counter, (abbreviation, list) in enumerate(data.items()):
            if counter + 1 > max_abbreviations:
                references = batch_editor.batch_replace(references, list[1], list[0], abbreviation)
    else:
        for counter, (abbreviation, list) in enumerate(data.items()):
            if counter + 1 < max_abbreviations:
                references = batch_editor.batch_replace(references, list[1], list[0], abbreviation)

    return references