from enum import Enum

class GroupingType(Enum):
    ATOZ = 0
    ZTOA = 1

def groupByRefType(refs, GroupingType):

    # create dict to store {reftype: [ref1, ref2, ref3, etc]}
    allrefs = {}
    for (reftype, key), fields in refs.items():
        if reftype not in allrefs.keys():
            #create new entry
            newRefsArray = []
            entry = ((reftype, key), fields)
            newRefsArray.append(entry)
            allrefs.update({reftype: newRefsArray})
        else:
            refsArray = allrefs.get(reftype)
            refsArray.append(((reftype, key), fields))

    #sort by tuple (alphabetically for now)
    strings_only_arr = [('string', allrefs.get("string"))]
    allrefs.pop("string")
    allrefs = sorted(allrefs.items(), reverse=GroupingType.value) #TODO: different types of sorting

    #get the refs from the [ref1, ref2, ref3, etc] array and put them in a dict to return
    result = {}

    for (key, refs) in strings_only_arr + allrefs:
        for (key, value) in refs:
            result.update({key:value})

    return result