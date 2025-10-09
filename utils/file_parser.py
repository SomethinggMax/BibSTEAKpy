from enum import Enum
from objects import BibFile, Reference, String, Comment, Preamble


class Token(Enum):
    REF_TYPE = 1
    KEY = 2
    DATA = 3
    EXTRA = 4


def parse_string(data):
    return data[1:-1]


def parse_fields(data, remove_whitespace_in_fields):
    fields = {}
    field_type = ""
    token = ""
    remove_whitespace = False
    curly_bracket_level = 0
    double_quotation_level = 0
    for line in data:
        for char in line:
            match char:
                case "=":
                    if curly_bracket_level == 0 and double_quotation_level == 0:
                        field_type = token.strip().lower()
                        token = ""
                        continue
                case ",":
                    if curly_bracket_level == 0 and double_quotation_level == 0:
                        if field_type in fields:
                            raise ValueError("Bib file contains duplicate fields in a single reference!")
                        fields[field_type] = token.strip()
                        token = ""
                        continue
                case "\"":
                    if curly_bracket_level == 0:
                        if double_quotation_level == 0:
                            double_quotation_level += 1
                        else:
                            double_quotation_level -= 1
                case "{":
                    curly_bracket_level += 1
                case "}":
                    curly_bracket_level -= 1
                case "\n":
                    if remove_whitespace_in_fields:
                        remove_whitespace = True
                        continue
                case " ":
                    if remove_whitespace:
                        continue
                case "#":
                    # print("String concatenation not yet supported!")
                    pass
            if remove_whitespace:
                remove_whitespace = False
                token += " "
            token += char
    if token != "":
        fields[field_type] = token.strip()
    return fields


def parse_bib(file_name, remove_whitespace_in_fields) -> BibFile:
    result = BibFile(file_name)

    with open(file_name, encoding='utf-8') as file:
        token = ""
        comment = ""
        ref_type = ""
        key = ""
        curly_bracket_level = 0
        token_type = Token.EXTRA
        for line in file:
            for char in line:
                match char:
                    case "@":
                        if token_type == Token.EXTRA:
                            comment = token.strip()
                            token = ""
                            token_type = Token.REF_TYPE
                            continue
                    case "{":
                        curly_bracket_level += 1
                        if token_type == Token.REF_TYPE:
                            ref_type = token.lower()
                            token = ""
                            token_type = Token.KEY
                            if ref_type == "comment" or ref_type == "preamble":
                                token_type = Token.DATA
                            continue
                    case "}":
                        curly_bracket_level -= 1
                        if token_type == Token.DATA:
                            if curly_bracket_level == 0:
                                token = token.strip()
                                if ref_type == "comment":
                                    result.content.append(Comment(token))
                                elif ref_type == "preamble":
                                    result.content.append(Preamble(token))
                                elif ref_type == "string":
                                    result.content.append(String(comment, key, parse_string(token)))
                                else:
                                    reference = Reference(comment, ref_type, key)
                                    fields = parse_fields(token, remove_whitespace_in_fields)
                                    for field, field_value in fields.items():
                                        setattr(reference, field, field_value)
                                    result.content.append(reference)
                                token = ""
                                token_type = Token.EXTRA
                                continue
                    case "," | "=":
                        if token_type == Token.KEY:
                            key = token.strip()
                            token = ""
                            token_type = Token.DATA
                            continue
                token += char
    result.content.append(token)
    return result
