from objects import Reference
from utils import json_loader

def tag_refs(tag,reflist: list[Reference]):
    #get cite_keys only
    newarr = [ref.cite_key for ref in reflist]

    # add the new tagged references
    tags = json_loader.load_tags()
    if tag in tags.keys():
        citekeyarr = tags[tag]
        for citekey in newarr:
            if citekey not in citekeyarr:
                citekeyarr.append(citekey)
    else:
        tags[tag] = newarr

    json_loader.dump_tags(tags)  # replace content
    

def untag_refs(tag, citekeylist: list[str]):
    # remove the tagged references
    tags = json_loader.load_tags()
    if tag in tags.keys():
        citekeyarr = tags[tag]
        for citekey in citekeylist:
            if citekey in citekeyarr:
                citekeyarr.remove(citekey)

        # if we have removed all the citekeys in a tag, remove the full tag
        if citekeyarr == []:
            tags.pop(tag)
    else:
        return -1

    json_loader.dump_tags(tags)