from objects import BibFile
from utils import file_parser, file_generator

"""
returns a file with all the references with a certain field
"""
def filterByFieldExistence(bibFile: BibFile, field):

    relevant = [ref for ref in bibFile.get_references() if field in ref.get_fields().keys()]

    newFile = BibFile("allWith" + field)
    newFile.content = relevant

    return newFile

"""
returns a file with all the references with a certain value in a certain field
"""
def filterByFieldValue(bibFile: BibFile, field, value):
    relevant = [ref for ref in bibFile.get_references() if (field in ref.get_fields().keys() and value in ref.get_fields().get(field))]

    newFile = BibFile("allWith" + field + "Where" + value)
    newFile.content = relevant

    return newFile

"""
function that returns a file containing the references including a certain searchterm
"""
def search(bibFile: BibFile, searchterm):
    searchterm = str.lower(searchterm)
    array = []
    for ref in bibFile.get_references():
        if searchterm in ref.get_fields().keys():
            array.append(ref)
        for val in ref.get_fields().values():
            if searchterm in str.lower(val):
                array.append(ref)

    newFile = BibFile("searchedFor" + searchterm)
    newFile.content = array

    return newFile
