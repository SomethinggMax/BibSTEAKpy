from enum import Enum
from pprint import pprint

class GroupingType(Enum):
    ATOZ = 0
    ZTOA = 1

def groupByRefType(refs, order):
    order = int(order)
    # if GroupingType == 0:
    #     print("0")
    # else:
    #     print("1")


    # # create dict to store {reftype: [ref1, ref2, ref3, etc]}
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
            
    # pprint(allrefs)

    # #sort by tuple (alphabetically for now)
    if allrefs.get("string"):
        strings_only_arr = [('string', allrefs.get("string"))]
        allrefs.pop("string")
    else:
        strings_only_arr = []

    allrefs = sorted(allrefs.items(), reverse=order)
    # pprint(allrefs)

    # #get the refs from the [ref1, ref2, ref3, etc] array and put them in a dict to return
    result = {}

    # for (key, refs) in strings_only_arr + allrefs:
    #     for (key, value) in refs:
    #         result.update({key:value})

    # return result
    
    for (reftype, refs) in strings_only_arr + allrefs:
        for (key, value) in refs:
            result[key] = value

    return result