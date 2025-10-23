import os, json
from objects import BibFile
from utils import file_generator


def commit(bibfile: BibFile):
    file_path = bibfile.file_name
    file_name = file_path.split("\\")[-1]
    
    # Ensure there exists a hist directory for this file
    os.makedirs("history", exist_ok=True)
    hist_dir_path = os.path.join("history", f"hist_{file_name}")
    tracker_file_path = os.path.join(hist_dir_path, "tracker.json")
    os.makedirs(hist_dir_path, exist_ok=True)
    
    if not os.path.isfile(tracker_file_path):
        default_json = {"counter": 0, "last_time_modified": 2002}
        with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
            json.dump(default_json, tracker_file, ensure_ascii=False, indent=2)
    
    
    # do commit
    with open(tracker_file_path, "r", encoding="utf-8") as tracker_file:
        tracker = json.load(tracker_file)
        tracker_file.close()
        
    with open(tracker_file_path, "w", encoding="utf-8") as tracker_file:
        counter = tracker["counter"]
        tracker["counter"] = counter + 1
        commit_name = f"c_{counter + 1}_{file_name}"
        
        commit_file_path = os.path.join(hist_dir_path, commit_name)
        file_generator.generate_bib(bibfile, commit_file_path, True)
        
        json_str= json.dumps(tracker, indent=2)
        tracker_file.write(json_str)
        tracker_file.close()
        
        
        
    
    