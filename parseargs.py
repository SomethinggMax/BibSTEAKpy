import re

def parse_args(args) -> list:
    pattern = re.split(r'(\".*?\"|\'.*?\'|\[[^][]*]| )', args)
    pattern = [x for x in pattern if x.strip()]
    return pattern
    
parse_args("untag tag \"science core\" \'single quoted\' [\"kant\", \"science\"] etc jello etc2")