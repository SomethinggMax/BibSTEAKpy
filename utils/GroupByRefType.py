from enum import Enum
from objects import Reference, BibFile, String
from utils import file_generator, file_parser

class GroupingType(Enum):
    ATOZ = 0
    ZTOA = 1

def groupByRefType(bibfileObj: BibFile, enum: GroupingType):
    #get all references from the bib obj
    allRefs = [ref for ref in bibfileObj.content if type(ref) is Reference]
    allStrings = [ref for ref in bibfileObj.content if type(ref) is String]
    
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
        
    print(enum.value)
    refsByTypeDict = sorted(refsByTypeDict.items(), reverse= enum.value)

    #takes out all the references in order from the dict
    allRefsOrdered = [x for sublist in (y for (x,y) in refsByTypeDict) for x in sublist]

    newFile = BibFile("newfile")
    newFile.content = allStrings + allRefsOrdered

    bibfileObj.content = allStrings + allRefsOrdered


