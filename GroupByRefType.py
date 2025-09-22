
def groupByRefType(refs):

    # create dict to store {reftype: [ref1, ref2, ref3, etc]}
    allrefs = {}
    for (reftype, key), fields in refs.items():
        print(allrefs.keys())
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
    allrefs = sorted(allrefs.items()) #TODO: different types of sorting

    #get the refs from the [ref1, ref2, ref3, etc] array and put them in a dict to return
    result = {}
    for (key, refs) in allrefs:
        for (key, value) in refs:
            result.update({key:value})
    print(result)
    return result