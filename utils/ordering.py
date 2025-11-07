from enum import Enum
from objects import BibFile, Reference
from utils import file_parser, file_generator


class GroupingType(Enum):
    ATOZ = 0
    ZTOA = 1


def order_by_entry_type(bib_file: BibFile, enum: GroupingType):
    # get all references from the bib obj
    references_by_entry_types = references_to_entry_type_dict(bib_file.get_references())

    # sort dictionary either AtoZ or ZtoA
    references_by_entry_types = sorted(references_by_entry_types.items(), reverse=bool(enum.value))

    # takes all the inner refs from the sub-lists into one big list
    ordered_references = [x for sublist in (y for (x, y) in references_by_entry_types) for x in sublist]

    # replace the old content by the new content
    # order: preambles, strings, references, comments, remaining entries
    bib_file.content = (bib_file.get_preambles() + bib_file.get_strings()
                        + ordered_references + bib_file.get_comments() + bib_file.get_remaining_entries())


def references_to_entry_type_dict(references: [Reference]):
    # define dict with structure: {entry_type: [reference1, reference2, reference3]}
    entry_type_dict = {}
    for reference in references:
        fields = reference.get_fields()
        entry_type = fields["entry_type"]

        if entry_type not in entry_type_dict.keys():
            entry_type_dict[entry_type] = [reference]
        else:
            reference_array = entry_type_dict.get(entry_type)
            reference_array.append(reference)

    return entry_type_dict


# JUST FOR TESTING
if __name__ == '__main__':
    test_file = file_parser.parse_bib("../bib_files/biblatex-examples.bib")
    order_by_entry_type(test_file, GroupingType.ZTOA)
    file_generator.generate_bib(test_file, "../bib_files/bib-examples-grouped.bib")
