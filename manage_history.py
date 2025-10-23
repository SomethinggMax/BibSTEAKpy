import os, json
from objects import BibFile
from utils import file_generator, file_parser

RESET = "\033[0m"; RST = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"; M = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

def print_in_yellow(arg):
    print(f"{YELLOW}{arg}{RESET}")

def delete_branch(hist_dir_path, file_name, lower_bound, upper_bound):
    for index in range(lower_bound, upper_bound + 1):
        file_name_deletion =  f"c_{index}_{file_name}"
        deletion_path = os.path.join(hist_dir_path, file_name_deletion)
        os.remove(deletion_path)


def commit(bibfile: BibFile):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    
    # Ensure there exists a hist directory for this file
    os.makedirs("history", exist_ok=True)
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    os.makedirs(hist_dir_path, exist_ok=True)
    
    if not os.path.isfile(tracker_file_path):
        default_json = {"counter": 0, "branch_tip": 0, "head": 0, "last_time_modified": 2002}
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            json.dump(default_json, tracker_file, ensure_ascii=False, indent=2)
    
    
    # do commit
    with open(tracker_file_path, "r", encoding="utf-8") as tracker_file:
        tracker = json.load(tracker_file)
        tracker_file.close()
        
    with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
        counter = tracker["counter"]
        
        if tracker["branch_tip"] == tracker["head"]:
            tracker["counter"] = counter + 1
            tracker["branch_tip"] = counter + 1
            tracker["head"] = counter + 1
            
            commit_name = f"c_{tracker['head']}_{file_name}"
            
            commit_file_path = os.path.join(hist_dir_path, commit_name)
            file_generator.generate_bib(bibfile, commit_file_path, True)
            
            json_str= json.dumps(tracker, indent=2)
            
        else:
            delete_branch(hist_dir_path, file_name, tracker["head"] + 1, tracker["branch_tip"])
            
            tracker["counter"] = tracker["head"] + 1
            tracker["branch_tip"] = tracker["head"] + 1
            tracker["head"] = tracker["head"] + 1
            
            
            commit_name = f"c_{tracker['head']}_{file_name}"
            commit_file_path = os.path.join(hist_dir_path, commit_name)
            file_generator.generate_bib(bibfile, commit_file_path, True)
            json_str= json.dumps(tracker, indent=2)
            
            
        
        tracker_file.write(json_str)
        tracker_file.close()
        
        
def undo(bibfile: BibFile, step=1):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    
    if not os.path.isdir(hist_dir_path):
        print_in_yellow("There is no history to undo - please commit a change first!")
        return 
    

    with open(tracker_file_path, "r", encoding="utf-8") as tracker_file:
        tracker = json.load(tracker_file)
        tracker_file.close()
    
    counter = tracker["counter"]
    branch_tip = tracker["branch_tip"]
    head = tracker["head"]
    if head - step >= 1 and head <= branch_tip:
        tracker["head"] = head - step
        
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            past_commit_name = f"c_{tracker['head']}_{file_name}"
            past_file_path = os.path.join(hist_dir_path, past_commit_name)
            past_bib_file = file_parser.parse_bib(past_file_path, True)
            file_generator.generate_bib(past_bib_file, file_path, True)
            
            json_str= json.dumps(tracker, indent=2)
            tracker_file.write(json_str)
            
            tracker_file.close()
    elif head == 1:
        print_in_yellow("You cannot undo anymore - you reached the first change of the branch!")
        return
    elif head > 1 and head - step < 1:
        maximum_step = head - 1
        print_in_yellow(f"The undo step is to large! - The maximum step allowed is {maximum_step}")
        return
        
    
        
def redo(bibfile: BibFile, step=1):
    step = step
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    
    if not os.path.isdir(hist_dir_path):
        print_in_yellow("There is no history to redo - please commit a change first!")
        return 
    
    
    with open(tracker_file_path, "r", encoding="utf-8") as tracker_file:
        tracker = json.load(tracker_file)
        tracker_file.close()
        
    branch_tip = tracker["branch_tip"]
    head = tracker["head"]
    
    if head >= 1 and head + step <= branch_tip:
        tracker["head"] = head + step
        
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            future_commit_name = f"c_{tracker['head']}_{file_name}"
            future_file_path = os.path.join(hist_dir_path, future_commit_name)
            future_bib_file = file_parser.parse_bib(future_file_path, True)
            file_generator.generate_bib(future_bib_file, file_path, True)
            
            json_str= json.dumps(tracker, indent=2)
            tracker_file.write(json_str)
            tracker_file.close()
            
    elif head == branch_tip:
        print_in_yellow("You are at the top of the history branch - You cannot redo anymore!")
        return
    elif head < branch_tip and head + step > branch_tip:
        maximum_step = branch_tip - head
        print_in_yellow(f"The redo step is to large! - The maximum step allowed is {maximum_step}")
        return
        
        

        
        
        
    
    