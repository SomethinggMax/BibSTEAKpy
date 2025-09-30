from enum import Enum
from objects import Reference

class GroupingType(Enum):
    ATOZ = 0
    ZTOA = 1

def groupByRefType(bibfileObj):
    #get all references from the bib obj
    allRefs = [ref for ref in bibfileObj.content if type(ref) is Reference]
    
    for ref in allRefs:


    return newBibfileObj