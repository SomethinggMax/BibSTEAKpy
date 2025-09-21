import pprint
import file_parser


result = file_parser.parse_bib("biblatex-examples.bib")
test = file_parser.parse_bib("bibtests.bib")

pprint.pprint(result)
print(test)

# Some examples on how to access information from the dictionary.
# print(result[("book", "augustine")]["author"])
# print(result[("book", "cicero")]["annotation"])

