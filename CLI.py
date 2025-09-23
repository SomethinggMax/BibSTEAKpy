import cmd
import os
import shutil
import json
import file_parser
import batch_editor
import file_generator
from pprint import pprint
from GroupByRefType import groupByRefType
import abbreviations_exec
import tkinter as tk
from tkinter.filedialog import askopenfilename
import tkinter as tk
from tkinter import filedialog
from sub_bib import sub_bib
import ast
from order_by_field import order_by_field

GREEN = "\033[92m"
RESET = "\033[0m"
RED         = "\033[31m"
GREEN       = "\033[32m"
YELLOW      = "\033[33m"
BLUE        = "\033[34m"
MAGENTA     = "\033[35m"
CYAN        = "\033[36m"
WHITE       = "\033[37m"

def print_in_green(arg):
    print(f"{GREEN}{arg}{RESET}")

CONFIG_FILE = "config.json"

COMMANDS = [("help", "Display the current menu"),
            ("load", "Load a particular file into the working directory"),
            ("set_directory <absolte/path/to/wd>", "Choose the ABSOLUTE path to a working directory"),
            ("list", "See all the bib files in the working directory"),
            ("wd", "Get current working directory"),
            ("abbreviations", "Display all abbreviations"),
            ("view <filename>", "View the content of a certain .bib file from your chosen working directory"),
            ("quit", "Close the BibSteak CLI"),
            ("refgroup <filename> <order>" , "Group and order based on entry type"),
            ("expand <filename>" , "Expand all abbreviations in the file"),
            ("collapse <filename>" , "Collapse all abbreviations in the file"),
            ("batch_replace <filename> <fields> <old string> <new string>", "Replace all occurrences in given fields"),
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
    
def display_help_commands():
    for command in COMMANDS:
        print(command[0], (60 - len(command[0]))*" ", command[1])
        
    print("")
    
def display_abbreviations():
    with open("abbreviations.json", "r") as f:
        abreviations = json.load(f)
        for key, value in abreviations.items():
            print(f"{key} {(15-len(key))*' '} {value[0]}")
        

class CLI(cmd.Cmd):
    intro = f"""{MAGENTA}
    _____  ___     _____ _______ ______         __  __       _____ __     ______ 
    |  _ \(_) |   / ____|__   __|  ____|   /\   | |/ /      / ____| |    |_   _|
    | |_) |_| |__| (___    | |  | |__     /  \  | ' /      | |    | |      | |  
    |  _ <| | '_ \___ \    | |  |  __|   / /\ \ |  <       | |    | |      | |  
    | |_) | | |_) |___) |  | |  | |____ / ____ \| . \      | |____| |____ _| |_ 
    |____/|_|_.__/_____/   |_|  |______/_/    \_\_|\_\      \_____|______|_____|
    {RESET}                                                                                                                                                                                                                
    Welcome to BibStShell! Type 'help' to list commands.
    The current/last working directory is {get_working_directory_path()}
    If you want to change it use the set_directory <source_directory> command
    and add the absolute path as an argument.
    """   
    prompt = f"{MAGENTA}BibSTEAK CLI >:{RESET}"
    completekey = "tab"
    doc_header   = "Available commands:"
    undoc_header = "Other commands:"
    misc_header  = "Topics:"
    ruler        = "-"
    

        
    # commands  
    def do_load(self, arg):
        load_file_to_storage(arg)
        
    def do_list(self, arg):
        try:
            folder_path = get_working_directory_path()
            
            if os.listdir(folder_path):
                index = 1
                print(f"Bib files in {folder_path}")
                for filename in os.listdir(folder_path):
                    full_path = os.path.join(folder_path, filename)
                    if os.path.isfile(full_path):   # ignore subfolders
                        print(f"{BLUE}[{index}] {RESET}", filename)
                    index += 1
            else:
                print("The working directory is empty!")
                    
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        
    def do_wd(self, arg):
        print(f"{BLUE}Current working directory: {get_working_directory_path()}{RESET}")
        
    def do_set_directory(self, wd_path): 
        
        try:
            if os.path.exists(wd_path) == False:
                raise Exception(f"Path not found: {wd_path}")
            
            with open("config.json", "r") as f:
                config = json.load(f)
                
            config["working_directory"] = wd_path
                
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
                
            print_in_green(f"Directory successfuly set to {wd_path}")
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def do_help(self, arg):
        display_help_commands()

    def do_abbreviations(self, arg):
        display_abbreviations()
        
    def do_quit(self, arg):
        print(f"{GREEN}Bye! - Shell closed{RESET}")
        return True  # returning True exits the loop
    
    def do_view(self, arg):
        try:
            path = os.path.join(get_working_directory_path(), arg)
            with open(path, "r") as f:
                for line in f:
                    print(f"{YELLOW}|>  {RESET}", line, end="")
                    
            print("\n")
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
                
    def do_batch_replace(self, args):
        try:
            filename, fields, old_string, new_string = args.split()  
            print(filename, fields, old_string, new_string)
            
            # working_direcory =
            path = os.path.join(get_working_directory_path(), filename)
            reference_entries = file_parser.parse_bib(path, False)
            
            batch_editor.batch_replace(reference_entries, fields, old_string, new_string)
            file_generator.generate_bib(path, reference_entries, 15)
            
            print_in_green("Batch replace has been done successfuly!")
            
        except Exception as e:
            print(f"Unexpected error: {e}")
        
    def do_refgroup(self, args):
        try:
            filename, order = args.split()
            path = os.path.join(get_working_directory_path(), filename)
            reference_entries = file_parser.parse_bib(path, False)
            result = groupByRefType(reference_entries, order)
            file_generator.generate_bib(path, result, 15)
            
            print_in_green("Grouping by reference done successfuly!")
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        
    def do_expand(self, arg):
        try:
            filename = arg
            path = os.path.join(get_working_directory_path(), filename)
            reference_entries = file_parser.parse_bib_helper(path, False)
            examples_edited = abbreviations_exec.execute_abbreviations(reference_entries, True, 1000)
            file_generator.generate_bib_helper(path, examples_edited, 15)
            
            print_in_green("Expanding abbreviations has been done successfuly!")
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        
    def do_collapse(self, arg):
        try:
            filename = arg
            path = os.path.join(get_working_directory_path(), filename)
            reference_entries = file_parser.parse_bib_helper(path, False)
            examples_edited = abbreviations_exec.execute_abbreviations(reference_entries, False, 1000)
            file_generator.generate_bib_helper(path, examples_edited, 15)
            
            print_in_green("Collapsing abbreviations has been done successfuly!")
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        
    def do_sub(self, args):
        try:
            filename, new_filename, entry_types = args.split()
            entry_types_list = ast.literal_eval(entry_types)
            # print(type(entry_types))
            path = os.path.join(get_working_directory_path(), filename)
            file = file_parser.parse_bib(path, True)
            sub_file = sub_bib(file, entry_types_list)
            # sub_file = sub_bib(file, ['article'])
            # print(sub_file)
            new_path = os.path.join(get_working_directory_path(), new_filename)
            # print(new_path)
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            file_generator.generate_bib(new_path, sub_file, 15)  
                  
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
                
    def do_order(self, args):
        try:
            def str_to_bool(s: str) -> bool:
                return s.strip().lower() in ("True", "true", "1", "yes", "y", "on")
            
            filename, field, descending = args.split()
            descending = str_to_bool(descending)
            
            # print(type(entry_types))
            path = os.path.join(get_working_directory_path(), filename)
            file = file_parser.parse_bib(path, True)
            order_by_field(file, field, descending)
            file_generator.generate_bib(path, file, 15)
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        
    def default(self, line):
        print('Command not found!')
        
    def emptyline(self):
        pass
        
if __name__ == "__main__":
    CLI().cmdloop()
