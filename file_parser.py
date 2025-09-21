from enum import Enum


class Token(Enum):
    REF_TYPE = 1
    KEY = 2
    DATA = 3
    EXTRA = 4


def parse_string(data):
    return data[1:-1]


def parse_tags(data):
    dictionary = {}
    field_type = ""
    token = ""
    curly_bracket_level = 0
    double_quotation_level = 0
    for line in data:
        for char in line:
            match char:
                case "=":
                    if curly_bracket_level == 0 and double_quotation_level == 0:
                        field_type = token.strip()
                        token = ""
                        continue
                case ",":
                    if curly_bracket_level == 0 and double_quotation_level == 0:
                        dictionary[field_type] = token.strip()
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
                case "#":
                    print("String concatenation not yet supported!")
            token += char
    if token != "":
        dictionary[field_type] = token.strip()
    return dictionary


def parse_bib(file_name):
    references = {}

    with open(file_name, "r+") as file:
        token = ""
        ref_type = ""
        key = ""
        curly_bracket_level = 0
        token_type = Token.EXTRA
        for line in file:
            for char in line:
                match char:
                    case "@":
                        if token_type == Token.EXTRA:
                            token = ""
                            token_type = Token.REF_TYPE
                            continue
                    case "{":
                        curly_bracket_level += 1
                        if token_type == Token.REF_TYPE:
                            ref_type = token.lower()
                            token = ""
                            token_type = Token.KEY
                            continue
                    case "}":
                        curly_bracket_level -= 1
                        if token_type == Token.DATA:
                            if curly_bracket_level == 0:
                                if ref_type == "preamble" or ref_type == "comment":
                                    print("Skipping ", ref_type, "entry")
                                    token = ""
                                    token_type = Token.EXTRA
                                    continue
                                token = token.strip()
                                if ref_type == "string":
                                    references[(ref_type, key)] = parse_string(token)
                                else:
                                    references[(ref_type, key)] = parse_tags(token)
                                token = ""
                                token_type = Token.EXTRA
                                continue
                    case "," | "=":
                        if token_type == Token.KEY:
                            key = token.strip()
                            token = ""
                            token_type = Token.DATA
                            continue
                    case "\n":
                        continue
                token += char
    return references
