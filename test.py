from enum import Enum
import pprint


class Token(Enum):
    REF_TYPE = 1
    KEY = 2
    DATA = 3


references = {}

with open("biblatex-examples.bib", "r+") as file:
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
                    references[(ref_type, key)] = token
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

pprint.pprint(references)
