from enum import Enum
import pprint


class Token(Enum):
    REF_TYPE = 1
    KEY = 2
    DATA = 3


def parse_string(data):
    return data[1:-1]


def parse_tags(data):
    dictionary = {}
    field_type = ""
    token = ""
    curly_bracket_level = 0
    for line in data:
        for char in line:
            if char == "=" and curly_bracket_level == 0:
                field_type = token.strip()
                token = ""
                continue
            if char == "," and curly_bracket_level == 0:
                dictionary[field_type] = token.strip()
                token = ""
                continue
            if char == "{":
                curly_bracket_level += 1
                if curly_bracket_level == 1:
                    continue
            if char == "}":
                curly_bracket_level -= 1
                if curly_bracket_level == 0:
                    continue
            token += char
    return dictionary


def parse_bib(file_name):
    references = {}

    with open(file_name, "r+") as file:
        token = ""
        ref_type = ""
        key = ""
        token_type = Token.REF_TYPE
        for line in file:
            for char in line:
                if char == "@":
                    if token_type == Token.DATA:
                        ref_type = ref_type.lower()
                        if ref_type == "preamble" or ref_type == "comment":
                            print("Skipping ", ref_type, "entry")
                            token = ""
                            token_type = Token.REF_TYPE
                            continue
                        token = token.strip()[:-1]
                        if ref_type == "string":
                            references[(ref_type, key)] = parse_string(token)
                        else:
                            references[(ref_type, key)] = parse_tags(token)
                        token = ""
                        token_type = Token.REF_TYPE
                    continue
                if char == "{":
                    if token_type == Token.REF_TYPE:
                        ref_type = token
                        token = ""
                        token_type = Token.KEY
                        continue
                if char == "," or char == "=":
                    if token_type == Token.KEY:
                        key = token.strip()
                        token = ""
                        token_type = Token.DATA
                        continue
                if char == "#":
                    print("String concatenation not yet supported!")
                if char != "\n":
                    token += char
    return references


result = parse_bib("biblatex-examples.bib")

pprint.pprint(result)
