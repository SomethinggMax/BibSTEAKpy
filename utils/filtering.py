from objects import BibFile


def filterByFieldExistence(bibFile: BibFile, field):
    """
    returns a file with all the references with a certain field
    """

    relevant = [ref for ref in bibFile.get_references() if field in ref.get_fields().keys()]

    return -1 if not relevant else relevant


def filterByFieldValue(bibFile: BibFile, field, value):
    """
    returns a file with all the references with a certain value in a certain field
    """
    relevant = [ref for ref in bibFile.get_references() if
                (field in ref.get_fields().keys() and value in str.lower(ref.get_fields().get(field)))]

    return -1 if not relevant else relevant


def search(bibFile: BibFile, searchterm):
    """
    function that returns a file containing the references including a certain searchterm
    """
    searchterm = str.lower(searchterm)
    array = []
    for ref in bibFile.get_references():
        if searchterm in ref.get_fields().keys():
            array.append(ref)
        for val in ref.get_fields().values():
            if searchterm in str.lower(val):
                array.append(ref)

    return -1 if not array else array
