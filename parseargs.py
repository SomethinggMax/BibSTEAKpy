import re
import json

def parse_args(args) -> list:
    pattern = re.split(r'(\".*?\"|\'.*?\'|\[[^][]*]| )', args)
    pattern = [x for x in pattern if x.strip()]

    res = []
    for x in pattern:
        if(x.startswith('"') and x.endswith('"')):
            x=x.replace('"',"")
        elif(x.startswith('\'') and x.endswith('\'')):
            x=x.replace('\'',"")
        elif(x.startswith('[') and x.endswith(']')):
            x = json.loads(x)
        res.append(x)
 
    return res
    
parse_args("untag     tag \"double quoted thing\" \'single quoted\' [\"kant\", \"science\"] etc jello etc2")