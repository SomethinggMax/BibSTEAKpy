from enum import Enum
from objects import Reference
from objects import BibFile

class GroupingType(Enum):
    ATOZ = 0
    ZTOA = 1

def groupByRefType(bibfileObj):
    #get all references from the bib obj
    allRefs = [ref for ref in bibfileObj.content if type(ref) is Reference]
    
    #define dict with structure: {reftype: [refobj1,refobj2,refobj3]}
    refsByTypeDict = {}
    for ref in allRefs:
        fieldsDict = ref.get_fields()
        entryType = fieldsDict["entry_type"]

        if (entryType) not in refsByTypeDict.keys():
            refsByTypeDict[entryType] = [ref]
        else:
            refArray = refsByTypeDict.get(entryType)
            refArray.append(ref)
        
    refsByTypeDict = sorted(refsByTypeDict.items())

    #takes out all the references in order from the dict
    newnewlist = [x for sublist in (y for (x,y) in refsByTypeDict) for x in sublist]
    print(newnewlist)

    newFile = BibFile("newfile")
    newFile.content = newnewlist

    return newFile

