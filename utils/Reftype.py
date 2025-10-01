from enum import Enum
from objects import BibFile, Reference, String

class GroupingType(Enum):
    ATOZ = 0
    ZTOA = 1

def sortByReftype(bibfileObj: BibFile, enum: GroupingType):
    #get all references from the bib obj
    allStrings = [ref for ref in bibfileObj.content if type(ref) is String]
    
    refsByTypeDict = reftypesToDict(BibFile)
        
    #sort dictionary either AtoZ or ZtoA
    refsByTypeDict = sorted(refsByTypeDict.items(), reverse= enum.value)

    #takes all the inner refs from the sub-lists into one big list
    allRefsOrdered = [x for sublist in (y for (x,y) in refsByTypeDict) for x in sublist]

    #replace the old content by the new content
    #notice how strings stay on top of the document
    bibfileObj.content = allStrings + allRefsOrdered


def reftypesToDict(bibfileObj: BibFile):
    #get all refs from file
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
    
    return refsByTypeDict

def filterBy(bibfileObj: BibFile, reftype: String):
    refsByTypeDict = refsByTypeDict(BibFile)

    if reftype not in refsByTypeDict.keys():
        print("error, reftype not found in this file")
        #TODO: throw error?
        return
    else:
        return [x for sublist in (y for (x,y) in refsByTypeDict if x == reftype) for x in sublist]
