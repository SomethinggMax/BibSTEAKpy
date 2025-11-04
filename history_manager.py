
# TODO: Make sure hashes do not collide
# TODO: Better handle exceptions in the CLI and success/failure messages
# TODO: Integrate timestamps and comments
# TODO: First File Change
# TODO: Improve history visualisation

import os, json
import time
import json
from objects import BibFile
from utils import file_generator, file_parser
from secrets import token_hex
from datetime import datetime

RESET = "\033[0m"; RST = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"; M = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

DEFAULT_JSON = {"parent_to_childs": {}, 
                "child_to_parent": {}, 
                "BOTTOM": "None", 
                "TOP": "None", 
                "current_parent": "None", 
                "timestamp": {},
                "comments": {}
                }

class Node(object):
    def __init__(self, name):
        self.name = name
        self.children = []

def timestamp_local():
    # local time, timezone-aware; safe for filenames (no colons)
    return datetime.now().astimezone().strftime("%H.%M.%S %d-%m-%Y")

def print_in_yellow(arg):
    print(f"{YELLOW}{arg}{RESET}")
   
   
def print_in_green(arg):
    print(f"{GREEN}{arg}{RESET}")
   
    
def get_json_object(tracker_file_path):
    with open(tracker_file_path, "r", encoding="utf-8") as tracker_file:
        tracker = json.load(tracker_file)
        tracker_file.close()
        
    return tracker


def initialise_history(bibfile: BibFile):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    
    # Ensure there exists a history and hist_filename directory structure
    os.makedirs("history", exist_ok=True)
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    os.makedirs(hist_dir_path, exist_ok=True)
    
    
    # Ensure that there is a tracker file
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    if not os.path.isfile(tracker_file_path):
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            json.dump(DEFAULT_JSON, tracker_file, ensure_ascii=False, indent=2)
    
    # Do commit
    tracker = get_json_object(tracker_file_path)
    has_file = any(os.path.isfile(os.path.join(hist_dir_path, name)) and name != "tracker.json" for name in os.listdir(hist_dir_path))
    
    if not has_file:
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            commit_name = f"{token_hex(16)}"
            tracker["timestamp"][commit_name] = timestamp_local()
            
            tracker["current_parent"] = commit_name
            tracker["timestamp"][commit_name] = timestamp_local()
            commit_file_path = os.path.join(hist_dir_path, commit_name)
            file_generator.generate_bib(bibfile, commit_file_path)
            
            tracker["BOTTOM"] = commit_name
            tracker["TOP"] = commit_name
            
            json_str= json.dumps(tracker, indent=2)
            tracker_file.write(json_str)
            tracker_file.close()
            
            
def commit(bibfile: BibFile):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    
    # Ensure there exists a history and hist_filename directory structure
    os.makedirs("history", exist_ok=True)
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    os.makedirs(hist_dir_path, exist_ok=True)
    
    # Ensure that there is a tracker file
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    if not os.path.isfile(tracker_file_path):
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            json.dump(DEFAULT_JSON, tracker_file, ensure_ascii=False, indent=2)
    
    # Do commit
    tracker = get_json_object(tracker_file_path)
    
    last_commit_path = os.path.join(hist_dir_path, tracker["current_parent"])
    if not same_commit(file_parser.parse_bib(last_commit_path), bibfile):
        if tracker["current_parent"] != tracker["TOP"]: # Tip of the branch
            print_in_yellow("Branching!") #TODO: REMOVE OR CLEARER MESSAGE
      
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            commit_name = f"{token_hex(16)}"
            tracker["timestamp"][commit_name] = timestamp_local()
            
            parent = tracker.get("current_parent", "__root__")  
            tracker.setdefault("current_parent", parent)
            tracker["parent_to_childs"].setdefault(parent, []).append(commit_name)
            tracker["child_to_parent"][commit_name] = tracker["current_parent"]
            
            tracker["current_parent"] = commit_name
            tracker["TOP"] = tracker["current_parent"]
            
            commit_file_path = os.path.join(hist_dir_path, commit_name)
            file_generator.generate_bib(bibfile, commit_file_path)
            json_str= json.dumps(tracker, indent=2)
                
            tracker_file.write(json_str)
            tracker_file.close()
        
    else:
        print_in_yellow("No changes detected relative to last commit.")
        

def undo(bibfile: BibFile, step=1):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    
    if not os.path.isdir(hist_dir_path):
        print_in_yellow("There is no history to undo - please commit a change first!")
        return 
    
    tracker = get_json_object(tracker_file_path)
    
    if tracker["current_parent"] != tracker["BOTTOM"]:
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            parent = tracker['child_to_parent'][tracker['current_parent']]
            past_commit_name = f"{parent}"
            past_file_path = os.path.join(hist_dir_path, past_commit_name)
            past_bib_file = file_parser.parse_bib(past_file_path)
            file_generator.generate_bib(past_bib_file, file_path)
            
            tracker["current_parent"] = parent
            json_str= json.dumps(tracker, indent=2)
            tracker_file.write(json_str)
            
    else:
        print_in_yellow("Reached the bottom of the history! - Cannot undo anymore")
    

def redo(bibfile: BibFile, step=1):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    
    if not os.path.isdir(hist_dir_path):
        print_in_yellow("There is no history to redo - please commit a change first!")
        return 
    
    tracker = get_json_object(tracker_file_path)
    
    if tracker["current_parent"] != tracker["TOP"]:
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            childs = tracker['parent_to_childs'][tracker['current_parent']]
            child = childs[-1]
            future_commit_name = f"{child}"
            future_file_path = os.path.join(hist_dir_path, future_commit_name)
            future_bib_file = file_parser.parse_bib(future_file_path)
            file_generator.generate_bib(future_bib_file, file_path)
            
            tracker["current_parent"] = child
            
            json_str= json.dumps(tracker, indent=2)
            tracker_file.write(json_str)
            tracker_file.close()
    else:
        print_in_yellow("Reached the top of the history! - Cannot redo anymore")


def checkout(bibfile: BibFile, commit_hash: str):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    
    if not os.path.isdir(hist_dir_path):
        print_in_yellow("There is no history to undo - please commit a change first!")
        return 
    
    checkout_path = os.path.join(hist_dir_path, commit_hash)
    
    if not os.path.isfile(checkout_path):
        print_in_yellow("Commit hash is not valid")
        return
    
    checkout_bib_file = file_parser.parse_bib(checkout_path)
    file_generator.generate_bib(checkout_bib_file, file_path)
    
    tracker = get_json_object(tracker_file_path)
    with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
        tracker["current_parent"] = commit_hash
        json_str= json.dumps(tracker, indent=2)
        tracker_file.write(json_str)
        tracker_file.close()
    
    
def history(bibfile: BibFile):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    
    # Ensure there exists a history and hist_filename directory structure
    os.makedirs("history", exist_ok=True)
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    os.makedirs(hist_dir_path, exist_ok=True)
    
    # Ensure that there is a tracker file
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    if not os.path.isfile(tracker_file_path):
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            json.dump(DEFAULT_JSON, tracker_file, ensure_ascii=False, indent=2)
    
    # Do commit
    tracker = get_json_object(tracker_file_path)
    parent_root = tracker["BOTTOM"]
    current_parent = tracker["current_parent"]
    adj_list = tracker["parent_to_childs"]
    tree = Node(parent_root)
    build_graph(tree, adj_list)
    print("")
    print_graph(tree, indent=0, parent=True, current_parent=current_parent)
    print_table(tracker)
    
    
def print_table(tracker):
    full_list = []
    for parent, childs in (tracker["parent_to_childs"]).items():
        if parent not in full_list:
            full_list.append(parent)
            
        for child in childs:
            if child not in full_list:
                full_list.append(child)
          
    print("\n")
    print(60 * "-")
    print(f"| {10*' '} COMMIT HASH {10*' '} | {4*' '}  TIMESTAMP {4*' '} |")
    print(60 * "-")
          
    for hash in full_list:
        print(f"| {hash}  |  {tracker['timestamp'][hash]} |")
        
    print(60 * "-")
    
    # TODO: If comment, display comment column as well
    
    
    
def build_graph(parent, adj_list):
    if parent.name in adj_list:
        for child_name in adj_list[parent.name]:
            parent.children.append(Node(child_name))
        
    for child in parent.children:
        build_graph(child, adj_list) 
        
        
def print_graph(tree, indent, parent=False, current_parent="None"):
    offset = 5
    visited = []
    if tree.name == current_parent:
        display_name = f"{MAGENTA}{tree.name}{RESET}"
    else:
        display_name = f"{WHITE}{tree.name}{RESET}"
        
    if parent == False:
        print(f"{MAGENTA}{(indent-1) * offset * ' '}|{1 * (offset-1) * '-'}| {RESET}{display_name}")
    else:
         print(f"{MAGENTA}| {display_name}{RESET}")
               
    for child in tree.children:
        print_graph(child, indent + 1, parent=False, current_parent=current_parent)
        
        
def same_commit(bib_file1: BibFile, bib_file2: BibFile):
    return bib_file1.content == bib_file2.content


def comment(bibfile: BibFile, commit_hash: str, comment: str):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    tracker = get_json_object(tracker_file_path)
    
    with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
        tracker["comments"][commit_hash] = comment
        json_str= json.dumps(tracker, indent=2)
        tracker_file.write(json_str)

    
def delete_history(bibfile: BibFile): 
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    
    # Ensure there exists a history and hist_filename directory structure
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    if not os.path.isdir(hist_dir_path):
        print_in_yellow("There is no history delete for this file")
        return 
    
    for root, dirs, files in os.walk(hist_dir_path, topdown=False):
        for f in files:
            os.remove(os.path.join(root, f))
        for d in dirs:
            os.rmdir(os.path.join(root, d))
            
    os.rmdir(hist_dir_path)
    
    

    
    
