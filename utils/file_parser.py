from enum import Enum
import utils.json_loader
from objects import BibFile, Reference, String, Comment, Preamble, Enclosure


class State(Enum):
    ENTRY_TYPE = 1
    KEY = 2
    FIELD_KEY = 3
    VALUE = 4
    QUOTATION_MARKS_ENCLOSURE = 5
    BRACES_ENCLOSURE = 6
    EXTRA = 7


def _parse_string(data):
    return data[1:-1]


def _add_field(fields, field_type, field_value):
    """
    Adds new field, with given field type and value.
    Raises error if the field already exists and the contents are not the same.
    """
    if field_type in fields and fields[field_type] != field_value:
        raise ValueError(f"Bib file contains duplicate {field_type} "
                         f"fields with different contents in a single reference!")
    fields[field_type] = field_value


def parse_bib(file_path, remove_newlines_in_fields=None) -> BibFile:
    """
    Parses the file at the file_path into a BibFile object.
    """
    if remove_newlines_in_fields is None:
        remove_newlines_in_fields = utils.json_loader.load_config().get("remove_newlines_in_fields", False)
    result = BibFile(file_path)

    with open(file_path, encoding='utf-8') as file:
        token = ""
        comment = ""
        entry_type = ""
        key = ""
        field_type = ""
        fields = {}
        ignore_next = False
        remove_whitespace = False
        braces_level = 0
        current_state = State.EXTRA
        for line in file:
            for char in line:
                if ignore_next:  # In case of escape sequences.
                    ignore_next = False
                    token += char
                    continue
                match char:
                    case "@":
                        if current_state == State.EXTRA:  # Start of a new entry
                            comment = token.strip()
                            token = ""
                            current_state = State.ENTRY_TYPE
                            continue
                    case "{":
                        if current_state == State.ENTRY_TYPE:
                            entry_type = token
                            token = ""
                            current_state = State.KEY  # For references and strings.
                            if entry_type.lower() == "comment" or entry_type.lower() == "preamble":
                                current_state = State.VALUE  # Preambles and comments don't have keys.
                            continue
                        elif current_state == State.VALUE:  # Start of an enclosure.
                            current_state = State.BRACES_ENCLOSURE
                            braces_level += 1
                        elif current_state == State.BRACES_ENCLOSURE:  # Enclosure inside enclosure.
                            braces_level += 1
                    case "=":
                        if current_state == State.KEY:  # Start of the long_form inside a string.
                            key = token.strip()
                            token = ""
                            current_state = State.VALUE
                            continue
                        elif current_state == State.FIELD_KEY:  # Start of the field_value
                            field_type = token.strip()
                            if " " and "\n" in field_type:
                                unsupported_comment = field_type.split("\n")[0]
                                raise ValueError(f"Parser does not support comments after field values: "
                                                 f"key: '{key}', comment: '{unsupported_comment}'")
                            token = ""
                            current_state = State.VALUE
                            continue
                    case ",":
                        if current_state == State.KEY:  # Start of fields inside reference.
                            key = token.strip()
                            token = ""
                            current_state = State.FIELD_KEY
                            continue
                        elif current_state == State.VALUE and entry_type.lower() != "comment":  # End of the field value.
                            _add_field(fields, field_type, token.strip())
                            token = ""
                            current_state = State.FIELD_KEY
                            continue
                    case "\"":
                        if current_state == State.VALUE:  # Start of enclosure.
                            current_state = State.QUOTATION_MARKS_ENCLOSURE
                        elif current_state == State.QUOTATION_MARKS_ENCLOSURE:  # End of enclosure.
                            current_state = State.VALUE
                    case "\\":
                        if current_state == State.QUOTATION_MARKS_ENCLOSURE:  # Escape sequence.
                            ignore_next = True
                    case "\n":
                        if current_state == State.VALUE or current_state == State.QUOTATION_MARKS_ENCLOSURE or current_state == State.BRACES_ENCLOSURE:
                            if remove_newlines_in_fields:
                                remove_whitespace = True
                                continue
                    case " ":
                        if remove_whitespace:
                            continue
                    case "}":
                        if current_state == State.FIELD_KEY or current_state == State.VALUE:  # End of reference.
                            # Can also come at the state of VALUE because the last comma is optional.
                            token = token.strip()
                            if entry_type.lower() == "comment":
                                result.content.append(Comment(token))
                                if comment != "":
                                    raise ValueError(f"Parser does not support comments above comment entries: "
                                                     f"comment entry: {token}, unsupported comment: {comment}")
                            elif entry_type.lower() == "preamble":
                                result.content.append(Preamble(token))
                                if comment != "":
                                    raise ValueError(f"Parser does not support comments above preamble entries: "
                                                     f"preamble entry: {token}, unsupported comment: {comment}")
                            elif entry_type.lower() == "string":
                                if token.startswith("{") and token.endswith("}"):
                                    enclosure = Enclosure.BRACES
                                elif token.startswith("\"") and token.endswith("\""):
                                    enclosure = Enclosure.QUOTATION_MARKS
                                else:
                                    raise ValueError(f"Bib file contains a string with invalid enclosure: {token}")
                                result.content.append(String(comment, key, _parse_string(token), enclosure))
                            else:
                                reference = Reference(comment, entry_type, key)
                                token = token.strip()
                                if token != "":
                                    if current_state == State.VALUE:  # Since a comma in the last field is optional.
                                        _add_field(fields, field_type, token)
                                    else:
                                        raise ValueError(f"Parser does not support comments after final field value: "
                                                         f"key: '{key}', comment: '{token}'")
                                for field, field_value in fields.items():
                                    setattr(reference, field, field_value)
                                result.content.append(reference)
                            token = ""
                            current_state = State.EXTRA
                            fields = {}
                            comment = ""
                            continue
                        elif current_state == State.BRACES_ENCLOSURE:
                            braces_level -= 1
                            if braces_level == 0:
                                current_state = State.VALUE
                if remove_whitespace:
                    remove_whitespace = False
                    token += " "  # Add a single space to replace all the removed whitespace.
                token += char
    result.content.append(token.strip())
    return result
