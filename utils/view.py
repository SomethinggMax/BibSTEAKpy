from objects import (BibFile, Reference, Comment, String)
from utils import file_parser
import re

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
GREY = "\033[030m"

def print_bibfile(bibfileobj: BibFile):
    for entry in bibfileobj.content:
        if type(entry) == String:
            print(f"@string{{{entry.abbreviation} {(10 - len(entry.abbreviation)) * ' '}= {entry.long_form}{((10 - len(entry.long_form)) * ' ' + "%" + entry.comment_above_string) if entry.comment_above_string else ""}}}")
        elif type(entry) == Reference:
            print("")
            print(f"@{entry.entry_type}{{{entry.cite_key}")
            for field in entry.get_fields():
                val = entry.get_fields().get(field)
                if field == "comment_above_reference":
                    if val != "":
                        print(f"{val}")
                    continue
                elif field == "entry_type" or field == "cite_key":
                    continue
                print(f"{field} {(15 - len(field)) * ' '}= {val}")
            print("}")

def print_bibfile_pretty(bibfileobj: BibFile):
    for entry in bibfileobj.content:
        if type(entry) == String:
            print(f"{YELLOW}@string {(16 - len("@string")) * ' '}{GREEN}{entry.abbreviation} {WHITE}{(8 - len(entry.abbreviation)) * ' '} {entry.long_form}{((10 - len(entry.long_form)) * ' ' + "%" + entry.comment_above_string) if entry.comment_above_string else ""}")
        elif type(entry) == Reference:
            print("")
            print(f"{BLUE}@{entry.entry_type}{(16 - len(entry.entry_type)) * ' '}{GREEN}{entry.cite_key}{WHITE}")
            for field in entry.get_fields():
                val = entry.get_fields().get(field)
                if field == "comment_above_reference":
                    if val != "":
                        print(f"{GREY}{val}{WHITE}")
                    continue
                elif field == "entry_type" or field == "cite_key":
                    continue
                if val.startswith("{"):
                    val = val[1:-1]
                print(f"{YELLOW}{field}{WHITE} {(15 - len(field)) * ' '} {val}")
        elif type(entry) == Comment:
            print(f"{GREY}% {entry.comment}{WHITE}")

def print_bibfile_short(bibfileobj: BibFile):
    print(f"{BLUE}ENTRY TYPE {(15 - len("entry type")) * ' '}{GREEN}CITE KEY {(20 - len("cite key")) * ' '}{WHITE}TITLE{(30 - len("TITLE")) * ' '} AUTHOR{(30 - len("AUTHOR")) * ' '} YEAR")
    print("")
    for entry in bibfileobj.get_references():
        things = [entry.get_fields().get("title"), entry.get_fields().get("author"), entry.get_fields().get("year")]
        str = f"{BLUE}@{entry.entry_type} {(15 - 1 - len(entry.entry_type)) * ' '}{GREEN}{entry.cite_key} {(20 - len(entry.cite_key)) * ' '}{WHITE}"
        for thing in things:
            if thing != None:
                if thing.startswith("{"):
                    thing = thing[1:-1]
                thing = thing.replace('\n', ' ').replace('\r', '')
                thing = re.sub(' +', ' ', thing)
                if len(thing) > 30:
                    thing = thing[:27] + ".. "
                str += f"{thing} {(30 - len(thing)) * ' '}"
            else:
                if thing != entry.get_fields().get("year"):
                    str += f"{31  * ' '}"
        print(str)

#TODO
def print_refarray_pretty(refarray: list[Reference]):
    return

            
                
# path = "C:/Users/Gebruiker/Downloads/test folder/science.bib"
# bibfileobj = file_parser.parse_bib(path, False)
# print_bibfile_pretty(bibfileobj)
        
