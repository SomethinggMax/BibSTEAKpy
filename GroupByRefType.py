
def groupByRefType(refs):
    print(refs)
    print("hellooo")
    allrefs = {} #create dict to store {reftype: [ref1, ref2, ref3, etc]}
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
    allrefs = sorted(allrefs.items())

    result = {}
    for (key, refs) in allrefs:
        for (key, value) in refs:
            result.update({key:value})
    print(result)
    return result