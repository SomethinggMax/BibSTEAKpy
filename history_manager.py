
# TODO: Make sure hashes do not collide
# TODO: Better handle exceptions in the CLI and success/failure messages

import os, json
import time
import json
import rich

from objects import BibFile
from utils import file_generator, file_parser
from secrets import token_hex
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Tree
from rich.text import Text
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
    if not same_commit(file_parser.parse_bib(last_commit_path, True), bibfile):
        if tracker["current_parent"] != tracker["TOP"]: # Tip of the branch
            print("Branching!")
      
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
            past_bib_file = file_parser.parse_bib(past_file_path, True)
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
            future_bib_file = file_parser.parse_bib(future_file_path, True)
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
    
    checkout_bib_file = file_parser.parse_bib(checkout_path, True)
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
    
    class Demo(App):
        BINDINGS = [("q", "quit", "Quit")]  # press q to quit
        

        def compose(self) -> ComposeResult:
            if parent_root == current_parent:
                if parent_root in tracker["comments"]:
                    tree = Tree(Text(parent_root, "blue"), data = f"Commit Time: {tracker['timestamp'][parent_root]}\nComment: {tracker['comments'][parent_root]}")
                else:
                    tree = Tree(Text(parent_root, "blue"), data = f"Commit Time: {tracker['timestamp'][parent_root]}")
            else:
                if parent_root in tracker["comments"]:
                    tree = Tree(Text(parent_root, "white"), data = f"Commit Time: {tracker['timestamp'][parent_root]}\nComment: {tracker['comments'][parent_root]}")
                else:
                    tree = Tree(Text(parent_root, "white"), data = f"Commit Time: {tracker['timestamp'][parent_root]}")
                
            tree.root.expand()
            
            for child in adj_list[tracker["BOTTOM"]]:
                add_child_to_parent(tree.root, child, current_parent, tracker)
                
            for child in tree.root.children:
                update_tree(adj_list, child, tracker, current_parent)
            
            yield tree
            
        
        @on(Tree.NodeSelected)
        def show_data(self, event: Tree.NodeSelected) -> None:
            self.notify(str(event.node.data or "(no data)"))  # popup with the node's data
            
        @on(Tree.NodeCollapsed)
        def keep_open(self, event: Tree.NodeCollapsed) -> None:
            event.stop()           
            event.node.expand()    # reopen instantly
                    
    Demo().run()
    
    
def update_tree(adj_list, parent, tracker, current_parent):
    if label_from_node(parent) in adj_list:
        for child_name in adj_list[label_from_node(parent)]:
            add_child_to_parent(parent, child_name, current_parent, tracker)
            
        for child in parent.children:
            update_tree(adj_list, child, tracker, current_parent)
            
def add_child_to_parent(parent, child_name, current_parent, tracker):
    if child_name == current_parent:
        if child_name in tracker["comments"]:
            parent.add(Text(child_name, "blue"), data=f"Commit Time: {tracker['timestamp'][child_name]}\nComment: {tracker['comments'][child_name]}").expand()
        else:
            parent.add(Text(child_name, "blue"), data=f"Commit Time: {tracker['timestamp'][child_name]}").expand()
    else:
        if child_name in tracker["comments"]:
            parent.add(Text(child_name, "white"), data=f"Commit Time: {tracker['timestamp'][child_name]}\nComment: {tracker['comments'][child_name]}").expand()
        else:
            parent.add(Text(child_name, "white"), data=f"Commit Time: {tracker['timestamp'][child_name]}").expand()
    
    
def label_from_node(node) -> str:
    lab = node.label
    return lab.plain if isinstance(lab, Text) else str(lab)
        
        
def same_commit(bib_file1: BibFile, bib_file2: BibFile):
    same_r = same_references(bib_file1, bib_file2)
    same_c = same_comments(bib_file1, bib_file2)
    same_p = same_preambles(bib_file1, bib_file2)
    same_s = same_strings(bib_file1, bib_file2)
    same_ord = same_order(bib_file1, bib_file2)
    
    return same_r and same_c and same_p and same_s and same_ord


def same_order(bib_file1: BibFile, bib_file2:BibFile):
    references1 = bib_file1.get_references()
    references2 = bib_file2.get_references()
    
    for index in range(len(references2)):
        if references1[index].cite_key != references2[index].cite_key:
            return False
        
    return True

    
def same_references(bib_file1: BibFile, bib_file2:BibFile):
    entries1 = bib_file1.get_references()
    entries2 = bib_file2.get_references()

    string_entries1 = []
    for entry in entries1:
        fields = entry.get_fields()
        field_strings = [f"{key}: {value}" for key, value in fields.items() if
                         key not in ["comment_above_reference", "entry_type"]]
        string_entries1.append(field_strings)
        
        
    string_entries2 = []
    for entry in entries2:
        fields = entry.get_fields()
        field_strings = [f"{key}: {value}" for key, value in fields.items() if
                         key not in ["comment_above_reference", "entry_type"]]
        string_entries2.append(field_strings)
        
    return string_entries2 == string_entries1


def same_comments(bib_file1: BibFile, bib_file2:BibFile):
    comments1 = bib_file1.get_comments()
    comments2 = bib_file2.get_comments()
    
    string_comments1 = [com.comment for com in comments1]
    string_comments2 = [com.comment for com in comments2]
    
    return string_comments1 == string_comments2


def same_preambles(bib_file1: BibFile, bib_file2:BibFile):
    comments1 = bib_file1.get_preambles()
    comments2 = bib_file2.get_preambles()
    
    string_comments1 = [com.preamble for com in comments1]
    string_comments2 = [com.preamble for com in comments2]
    
    return string_comments1 == string_comments2
    
    
def same_strings(bib_file1: BibFile, bib_file2:BibFile):
    entries1 = bib_file1.get_strings()
    entries2 = bib_file2.get_strings()
    
    string_entries1 = []
    for entry in entries1:
        fields = entry.get_fields()
        field_strings = [f"{key}: {value}" for key, value in fields.items()]
        string_entries1.append(field_strings)

    string_entries2 = []
    for entry in entries2:
        fields = entry.get_fields()
        field_strings = [f"{key}: {value}" for key, value in fields.items()]
        string_entries2.append(field_strings)
        
    return string_entries2 == string_entries1


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
    
    

    
    
