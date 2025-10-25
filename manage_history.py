
# TODO: Detect no file changes
# TODO: Timestamp
# TODO: Make sure hashes do not collide
# TODO: Handle exceptions in the CLI and success/failure messages

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Tree
from rich.text import Text
from datetime import datetime


import os, json
import time
from objects import BibFile
from utils import file_generator, file_parser
from secrets import token_hex
import json
import networkx as nx
import matplotlib.pyplot as plt
import rich
# from rich.tree import Tree
# from rich import print

RESET = "\033[0m"; RST = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"; M = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

DEFAULT_JSON = {"parent_to_childs": {}, "child_to_parent": {}, "BOTTOM": "None", "TOP": "None", "current_parent": "None", "timestamp": {}}

def timestamp_local():
    # local time, timezone-aware; safe for filenames (no colons)
    return datetime.now().astimezone().strftime("%H.%M.%S %d-%m-%Y")

def print_in_yellow(arg):
    print(f"{YELLOW}{arg}{RESET}")
    
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
            file_generator.generate_bib(bibfile, commit_file_path, True)
            
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
            file_generator.generate_bib(bibfile, commit_file_path, True)
            json_str= json.dumps(tracker, indent=2)
                
            tracker_file.write(json_str)
            tracker_file.close()
        

    else:
        print_in_yellow("No changes detected.")
        
    # view_graph(tracker_file_path)
    # print_graph(bibfile)
        
     

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
            file_generator.generate_bib(past_bib_file, file_path, True)
            
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
        print_in_yellow("There is no history to undo - please commit a change first!")
        return 
    
    tracker = get_json_object(tracker_file_path)
    
    if tracker["current_parent"] != tracker["TOP"]:
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            childs = tracker['parent_to_childs'][tracker['current_parent']]
            child = childs[-1]
            future_commit_name = f"{child}"
            future_file_path = os.path.join(hist_dir_path, future_commit_name)
            future_bib_file = file_parser.parse_bib(future_file_path, True)
            file_generator.generate_bib(future_bib_file, file_path, True)
            
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
    
    tracker = get_json_object(tracker_file_path)
    
    checkout_path = os.path.join(hist_dir_path, commit_hash)
    checkout_bib_file = file_parser.parse_bib(checkout_path, True)
    file_generator.generate_bib(checkout_bib_file, file_path, True)
    
    with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
        tracker["current_parent"] = commit_hash
        json_str= json.dumps(tracker, indent=2)
        tracker_file.write(json_str)
        tracker_file.close()
    

def view_graph(tracker_file_path):
    with open(tracker_file_path, encoding="utf-8") as f:
        adj = json.load(f)["parent_to_childs"]

    G = nx.DiGraph((p, c) for p, kids in adj.items() for c in kids)

    # pick a root (in-degree 0) and layer by shortest-path
    root = next((n for n in G if G.in_degree(n) == 0), next(iter(G)))
    depth = nx.shortest_path_length(G, source=root)
    for n, d in depth.items():
        G.nodes[n]["layer"] = d

    # horizontal 
    pos = nx.multipartite_layout(G, subset_key="layer")

    # rotate 90 so layers are vertical 
    pos = {n: (y, -x) for n, (x, y) in pos.items()}

    nx.draw(G, pos, with_labels=True, arrows=True)
    plt.gca().invert_yaxis()  # put root near the top
    plt.tight_layout()
    plt.show()
    
    
# def history(bibfile: BibFile):
    
#     file_path = bibfile.file_name
#     file_name = file_path.split("\\")[-1]
    
#     # Ensure there exists a history and hist_filename directory structure
#     os.makedirs("history", exist_ok=True)
#     hist_dir_path = os.path.join("history", f"hist_{file_name}")
#     os.makedirs(hist_dir_path, exist_ok=True)
    
    
#     # Ensure that there is a tracker file
#     tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
#     if not os.path.isfile(tracker_file_path):
#         with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
#             json.dump(DEFAULT_JSON, tracker_file, ensure_ascii=False, indent=2)
    
#     # Do commit
#     tracker = get_json_object(tracker_file_path)
#     parent_root = tracker["BOTTOM"]
#     current_parent = tracker["current_parent"]
    
    
#     def dict_to_tree(d, label="root"):
#         t = Tree(label)
#         for k, v in d.items():
#             if isinstance(v, dict):
#                 t.add(dict_to_tree(v, str(k)))
#             else:
#                 t.add(f"{k}: {v}")
#         return t

#         data = {"src": {"core": {"util.py": None}, "app.py": None}, "README.md": None}
#         print(dict_to_tree(data, "project"))
        
        
#     adj_list = tracker["parent_to_childs"]
#     t = Tree(parent_root, guide_style="green", highlight=True)
#     add_to_tree(adj_list, t, t, current_parent)
    
    
#     # for p, childs in adj.items():
#     #     for c in childs:
#     #         print(c)
        
#     # t = Tree(label)
#     # john = t.add("John")
#     # john.add("Max")
#     # t.add(f"{p}: {c}" for p, childs in adj.items() for c in childs)
#     rich.print(t)
    
    
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
                tree = Tree(Text(parent_root, "blue"), data = f"Commit Time: {tracker['timestamp'][parent_root]}")
            else:
                tree = Tree(Text(parent_root, "white"), data = f"Commit Time: {tracker['timestamp'][parent_root]}")
                
            tree.root.expand()
            
            for child in adj_list[tracker["BOTTOM"]]:
                if child == current_parent:
                    tree.root.add(Text(child, "blue"), data = f"Commit Time: {tracker['timestamp'][child]}").expand()
                else:
                    tree.root.add(Text(child, "white"), data = f"Commit Time: {tracker['timestamp'][child]}").expand()
                
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
            if child_name == current_parent:
                parent.add(Text(child_name, "blue"), data=f"Commit Time: {tracker['timestamp'][child_name]}").expand()
            else:
                parent.add(Text(child_name, "white"), data=f"Commit Time: {tracker['timestamp'][child_name]}").expand()
                
                
            
        for child in parent.children:
            update_tree(adj_list, child, tracker, current_parent)
            
    
            
    
def label_from_node(node) -> str:
    lab = node.label
    return lab.plain if isinstance(lab, Text) else str(lab)
        
   
def add_to_tree(adj_list, t, parent, current_parent: str):
    
    # return t
    if parent.label in adj_list:
        for child in adj_list[parent.label]:
            if child == current_parent:
                parent.add(child, style="bold blue")
            else:
                parent.add(child, style="white")
        
        for child in parent.children:
            add_to_tree(adj_list, t, child, current_parent)
            # child.add("something")
        
    return t
        
    
    
    
# def same_commit(last_commit: BibFile, current_commit: BibFile) -> bool:
#     return False
    
    
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
    
    
    


    
    
