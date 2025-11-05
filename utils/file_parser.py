from enum import Enum
import utils.json_loader
from objects import BibFile, Reference, String, Comment, Preamble, Enclosure


class Token(Enum):
    REF_TYPE = 1
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
    if remove_newlines_in_fields is None:
        remove_newlines_in_fields = utils.json_loader.load_config().get("remove_newlines_in_fields", False)
    result = BibFile(file_path)

    with open(file_path, encoding='utf-8') as file:
        token = ""
        comment = ""
        ref_type = ""
        key = ""
        field_type = ""
        fields = {}
        ignore_next = False
        remove_whitespace = False
        braces_level = 0
        token_type = Token.EXTRA
        for line in file:
            for char in line:
                if ignore_next:
                    ignore_next = False
                    token += char
                    continue
                match char:
                    case "@":
                        if token_type == Token.EXTRA:
                            comment = token.strip()
                            token = ""
                            token_type = Token.REF_TYPE
                            continue
                    case "{":
                        if token_type == Token.REF_TYPE:
                            ref_type = token
                            token = ""
                            token_type = Token.KEY
                            if ref_type.lower() == "comment" or ref_type.lower() == "preamble":
                                token_type = Token.VALUE
                            continue
                        elif token_type == Token.VALUE:
                            token_type = Token.BRACES_ENCLOSURE
                            braces_level += 1
                        elif token_type == Token.BRACES_ENCLOSURE:
                            braces_level += 1
                    case "=":
                        if token_type == Token.KEY:
                            key = token.strip()
                            token = ""
                            token_type = Token.VALUE
                            continue
                        elif token_type == Token.FIELD_KEY:
                            field_type = token.strip()
                            if " " and "\n" in field_type:
                                unsupported_comment = field_type.split("\n")[0]
                                raise ValueError(f"Parser does not support comments after field values: "
                                                 f"key: '{key}', comment: '{unsupported_comment}'")
                            token = ""
                            token_type = Token.VALUE
                            continue
                    case ",":
                        if token_type == Token.KEY:
                            key = token.strip()
                            token = ""
                            token_type = Token.FIELD_KEY
                            continue
                        elif token_type == Token.VALUE and ref_type.lower() != "comment":
                            _add_field(fields, field_type, token.strip())
                            token = ""
                            token_type = Token.FIELD_KEY
                            continue
                    case "\"":
                        if token_type == Token.VALUE:
                            token_type = Token.QUOTATION_MARKS_ENCLOSURE
                        elif token_type == Token.QUOTATION_MARKS_ENCLOSURE:
                            token_type = Token.VALUE
                    case "\\":
                        if token_type == Token.QUOTATION_MARKS_ENCLOSURE:
                            ignore_next = True
                    case "\n":
                        if token_type == Token.VALUE or token_type == Token.QUOTATION_MARKS_ENCLOSURE or token_type == Token.BRACES_ENCLOSURE:
                            if remove_newlines_in_fields:
                                remove_whitespace = True
                                continue
                    case " ":
                        if remove_whitespace:
                            continue
                    case "}":
                        if token_type == Token.FIELD_KEY or token_type == Token.VALUE:
                            token = token.strip()
                            if ref_type.lower() == "comment":
                                result.content.append(Comment(token))
                                if comment != "":
                                    raise ValueError(f"Parser does not support comments above comment entries: "
                                                     f"comment entry: {token}, unsupported comment: {comment}")
                            elif ref_type.lower() == "preamble":
                                result.content.append(Preamble(token))
                                if comment != "":
                                    raise ValueError(f"Parser does not support comments above preamble entries: "
                                                     f"preamble entry: {token}, unsupported comment: {comment}")
                            elif ref_type.lower() == "string":
                                if token.startswith("{") and token.endswith("}"):
                                    enclosure = Enclosure.BRACES
                                elif token.startswith("\"") and token.endswith("\""):
                                    enclosure = Enclosure.QUOTATION_MARKS
                                else:
                                    raise ValueError(f"Bib file contains a string with invalid enclosure: {token}")
                                result.content.append(String(comment, key, _parse_string(token), enclosure))
                            else:
                                reference = Reference(comment, ref_type, key)
                                if token.strip() != "":
                                    _add_field(fields, field_type, token.strip())
                                for field, field_value in fields.items():
                                    setattr(reference, field, field_value)
                                result.content.append(reference)
                            token = ""
                            token_type = Token.EXTRA
                            fields = {}
                            comment = ""
                            continue
                        elif token_type == Token.BRACES_ENCLOSURE:
                            braces_level -= 1
                            if braces_level == 0:
                                token_type = Token.VALUE
                if remove_whitespace:
                    remove_whitespace = False
                    token += " "
                token += char
    result.content.append(token.strip())
    return result
