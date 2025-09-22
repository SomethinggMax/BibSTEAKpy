import cmd
import os
import shutil

STORAGE_FOLDER = "storage"
    
COMMANDS = [("help", "Display the current menu"),
            ("quit", "Close the BibSteakShell"),
            ("load", "Load a particular file into the program's storage"),
            ("storage", "See all the files which are curently in the storage"),
            ]


def load_file_to_storage(source_path):
    """
    Copy a file from source_path into the storage folder.
    Creates the folder if it doesn't exist.
    """
    try:
        os.makedirs(STORAGE_FOLDER, exist_ok=True)
        filename = os.path.basename(source_path)
        name, extension = os.path.splitext(filename)
        destination_path = os.path.join(STORAGE_FOLDER, filename)
        
        if extension == ".bib":
            shutil.copy(source_path, destination_path)

            print(f"File '{filename}' loaded into the storage successfuly!")
        else:
            raise ValueError(f"Invalid file extension: '{extension}'. Only .bib files are allowed.")
            
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
        folder = "storage"
        for filename in os.listdir(folder):
            full_path = os.path.join(folder, filename)
            if os.path.isfile(full_path):   # ignore subfolders
                print(filename)
                
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    
    

class MyTool(cmd.Cmd):
    intro = "Welcome to BibStShell! Type 'help' to list commands.\n"
    prompt = "BibStShell> "
    
    # commands
        
    def do_load(self, arg):
        load_file_to_storage(arg)
        
    def do_storage(self, arg):
        display_storage_files()
        
    def do_help(self, arg):
        display_help_commands()

    def do_quit(self, arg):
        print("Bye! - SHell closed")
        return True  # returning True exits the loop

if __name__ == "__main__":
    MyTool().cmdloop()
