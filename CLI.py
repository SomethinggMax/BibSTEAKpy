import cmd
import os
import shutil
import json

CONFIG_FILE = "config.json"

COMMANDS = [("help", "Display the current menu"),
            ("load", "Load a particular file into the working directory"),
            ("set_directory", "Configure a working directory"),
            ("storage", "See all the bib files in the working directory"),
            ("wd", "Get current working directory"),
            ("abbreviations", "Display all abbreviations"),
            ("quit", "Close the BibSteak CLI"),
            ]

def get_working_directory_path():
    with open("config.json", "r") as f:
        config = json.load(f)
        working_directory_path = config["working_directory"]
        return working_directory_path


def load_file_to_storage(source_path):
    """
    Copy a file from source_path into the storage folder.
    Creates the folder if it doesn't exist.
    """
    try:
        working_directory = get_working_directory_path()
        os.makedirs(working_directory, exist_ok=True)
        filename = os.path.basename(source_path)
        name, extension = os.path.splitext(filename)
        destination_path = os.path.join(working_directory, filename)
        
        if extension == ".bib":
            shutil.copy(source_path, destination_path)

            print(f"File '{filename}' loaded into the storage successfuly!")
        else:
            raise ValueError(f"Invalid file extension: '{extension}'. Only .bib files are allowed.")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    
    
def set_directory(absolute_working_directory_path):
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            
        config["working_directory"] = absolute_working_directory_path
            
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
            
        print(f"Directory successfuly set to {absolute_working_directory_path}")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
        
    
def display_help_commands():
    print(f"{'-'*30} All COMMANDS {'-'*30}")
    
    for command in COMMANDS:
        print(command[0], (15 - len(command[0]))*" ", command[1])
        
    print(f"{'-'*30}{'-'*len(' All COMMANDS ')}{'-'*30}")
    
    
def display_storage_files():
    try:
        folder = get_working_directory_path()
        for filename in os.listdir(folder):
            full_path = os.path.join(folder, filename)
            if os.path.isfile(full_path):   # ignore subfolders
                print(filename)
                
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    
    
def display_abbreviations():
    with open("abbreviations.json", "r") as f:
        abreviations = json.load(f)
        for key, value in abreviations.items():
            print(f"{key} {(15-len(key))*' '} {value}")
        

class CLI(cmd.Cmd):
    intro = f"""
    _____  ___     _____ _______ ______         __  __       _____ __     ______ 
    |  _ \(_) |   / ____|__   __|  ____|   /\   | |/ /      / ____| |    |_   _|
    | |_) |_| |__| (___    | |  | |__     /  \  | ' /      | |    | |      | |  
    |  _ <| | '_ \___ \    | |  |  __|   / /\ \ |  <       | |    | |      | |  
    | |_) | | |_) |___) |  | |  | |____ / ____ \| . \      | |____| |____ _| |_ 
    |____/|_|_.__/_____/   |_|  |______/_/    \_\_|\_\      \_____|______|_____|
                                                                                                                                                                                                                         
    Welcome to BibStShell! Type 'help' to list commands.
    The current/last working directory is {get_working_directory_path()}
    If you want to change it use the set_directory <source_directory> command
    and add the absolute path as an argument.
    """   
    prompt = "BibSTEAK CLI >: "
    
    # commands  
    def do_load(self, arg):
        load_file_to_storage(arg)
        
    def do_storage(self, arg):
        display_storage_files()
        
    def do_wd(self, arg):
        print(f"Current working directory: {get_working_directory_path()}")
        
    def do_set_directory(self, arg):
        set_directory(arg)
        
    def do_help(self, arg):
        display_help_commands()

    def do_abbreviations(self, arg):
        display_abbreviations()
        
    def do_quit(self, arg):
        print("Bye! - Shell closed")
        return True  # returning True exits the loop

if __name__ == "__main__":
    CLI().cmdloop()
