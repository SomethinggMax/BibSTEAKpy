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

def print_bibfile_pretty(bibfileobj: BibFile):
    for entry in bibfileobj.content:
        if type(entry) == String:
            print(f"{YELLOW}{var_w_space('@String', 16)}{GREEN}{var_w_space(entry.abbreviation, 8)}{WHITE}{entry.long_form}{(c_space(entry.long_form, 10) + '%' + entry.comment_above_string) if entry.comment_above_string else ''}")
        elif type(entry) == Reference:
            print_ref_pretty(entry)
        elif type(entry) == Comment:
            print(f"{GREY}% {entry.comment}{WHITE}")

def print_bibfile_short(bibfileobj: BibFile):
    print_refarray_short(bibfileobj.get_references())

def print_refarray_pretty(refarray: list[Reference]):
        for ref in refarray:
            print_ref_pretty(ref)

def print_refarray_short(refarray: list[Reference]):
    """
    Prints a shortform of the ref array
    For each ref it will print [reftype, citekey, title, author, year]
    """
    print(f"{BLUE}{var_w_space('ENTRY TYPE', 15)}{GREEN}{var_w_space('CITE KEY', 20)}{WHITE}{var_w_space('TITLE', 30)}{var_w_space('AUTHOR', 30)}YEAR")
    print(f"{BLUE}{15 * '.'} {GREEN}{20 * '.'} {WHITE}{30 * '.'} {30 * '.'} {4 * '.'}")

    for entry in refarray:
        #since title, author and year could be none, they get added dynamically
        fields = [entry.get_fields().get("title"), entry.get_fields().get("author"), entry.get_fields().get("year")]
        str = f"{BLUE}{var_w_space('@' + entry.entry_type, 15)}{GREEN}{var_w_space(entry.cite_key, 20)}{WHITE}"
        for field in fields:
            if field != None:
                #CLEANING INPUT (yes this is needlessly long)
                #strip the field of curly braces if there
                if field.startswith("{"):
                    field = field[1:-1]
                #remove breaklines for multiple line fields
                field = field.replace('\n', ' ').replace('\r', '')
                #remove multiple spaces
                field = re.sub(' +', ' ', field)
                #if the field is too long, truncate and add ".." at the end
                if len(field) > 30:
                    field = field[:28] + ".."

                #add the string
                if field == fields[-1]: 
                    str += field #if it is the last one, do not add the spaces at the end
                else: 
                    str += var_w_space(field, 30)
            else: #if the field is none add a bunch of spaces as a placeholder
                if field != fields[-1]:
                    str += f"{31  * ' '}"
        print(str)
            
def print_ref_pretty(ref: Reference):
    print("")
    print(f"{BLUE}{var_w_space('@' + ref.entry_type, 16)}{GREEN}{ref.cite_key}{WHITE}")
    for field in ref.get_fields():
        val = ref.get_fields().get(field)
        if field == "comment_above_reference":
            if val != "":
                print(f"{GREY}{val}{WHITE}")
            continue
        elif field == "entry_type" or field == "cite_key":
            continue
        if val.startswith("{"):
            val = val[1:-1]
        print(f"{YELLOW}{field}{WHITE}{c_space(field, 17)}{val}")

def c_space(var: str, spacelen: int):
    return (spacelen - len(var)) * ' '

def var_w_space(var: str, spacelen:int):
    return var + c_space(var, spacelen) + ' '
            
                
# path = "C:/Users/Gebruiker/Downloads/test folder/science.bib"
# bibfileobj = file_parser.parse_bib(path, False)
# print_bibfile_pretty(bibfileobj)
        
