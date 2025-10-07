import cmd
import os
import shutil
import json
import readline
from utils import merge

if os.name == "nt" and not hasattr(readline, "backend"):
    readline.backend = "unsupported"
import utils.batch_editor as batch_editor
import utils.file_generator as file_generator
from pprint import pprint
from utils.Reftype import sortByReftype
import utils.abbreviations_exec as abbreviations_exec
import utils
from utils.order_by_field import *
from utils.sub_bib import *
from utils.file_parser import *
from utils.file_generator import *
from utils.Reftype import *
from utils.order_by_field import *
from utils.batch_editor import *
from utils.abbreviations_exec import *
from utils.filtering import *
import ast

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"


def print_in_green(arg):
    print(f"{GREEN}{arg}{RESET}")

def print_in_yellow(arg):
    print(f"{YELLOW}{arg}{RESET}")


CONFIG_FILE = "config.json"

COMMANDS = [
    ("help", "Display the current menu"),
    ("load", "Load a particular file into the working directory"),
    ("cd <directory>", "Changes the current working directory"),
    ("list", "See all the bib files in the working directory"),
    ("pwd", "Prints the working directory"),
    ("abb", "Display all abbreviations"),
    (
        "view <filename>",
        "View the content of a certain .bib file from your chosen working directory",
    ),
    ("quit", "Close the BibSteak CLI"),
    ("search <filename> <searchterm>", "Displays references with a certain searchterm"),
    (
        "rg <filename> <field>",
        "Group references of a bib file based on a certain field",
    ),
    ("filter <filename> <field>, [value]", "Displays references with a certain field (OPTIONAL: a value in that field)"),
    ("exp <filename>", "Expand all abbreviations in the file"),
    ("col <filename>", "Collapse all abbreviations in the file"),
    (
        "br <filename> <fields> <old string> <new string>",
        "Replace all occurrences in given fields",
    ),
    (
        "ord <filename> <field> [descending=False]",
        "Order the references based on a certain field",
    ),
    (
        "sub -e <filename> <new_filename>, <entry_types>",
        "Creates a sub .bib file with only specified entry " "types.",
    ),
    (
        "sub -t <filename> <new_filename>, <tags>",
        "Creates a sub .bib file with only references with specified " "tags.",
    ),
    (
        "mer <filename1> <filename2> <new_filename>",
        "Merge the references from two bib files into one file.",
    ),
    (
        "mer -all <new_filename>",
        "Merge all bib files in the current working directory.",
    ),
]


def completer(text, state):
    line = readline.get_line_buffer()
    split_line = line.strip().split()
    if len(split_line) <= 1:
        options = [cmd[0] for cmd in COMMANDS if cmd[0].startswith(text)]
    else:
        try:
            wd = get_working_directory_path()
            files = [
                f for f in os.listdir(wd) if f.endswith(".bib") and f.startswith(text)
            ]
            options = files
        except Exception:
            options = []
    if state < len(options):
        return options[state]
    else:
        return None


def get_working_directory_path():
    with open("config.json", "r") as f:
        config = json.load(f)
        working_directory_path = config["working_directory"]
        return working_directory_path


def get_bib_file_names(folder_path):
    files = []
    if os.listdir(folder_path):
        index = 1
        for filename in os.listdir(folder_path):
            full_path = os.path.join(folder_path, filename)
            _, extension = os.path.splitext(filename)
            if os.path.isfile(full_path) and extension == ".bib":
                files.append((filename, index))  # ignore subfolders
                index += 1
    return files


def check_extension(new_file_name):
    root, ext = os.path.splitext(new_file_name)
    if ext == "":
        new_file_name += ".bib"
    elif ext != ".bib":
        raise ValueError(
            "The new file name must have a .bib extension or no extension at all."
        )
    return new_file_name


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

            print(f"{GREEN}File '{filename}' loaded into the storage successfuly!")
        else:
            if extension == "":
                raise ValueError("File has no extension. Only .bib files are allowed.")
            else:
                raise ValueError(
                    f"Invalid file extension: '{extension}'. Only .bib files are allowed."
                )

    except ValueError as e:
        print(f"File Type Error: {e}")
        return None
    except FileNotFoundError as e:
        print(f"File Not Found Error: {e.filename} not found.")
        return None
    except PermissionError as e:
        print(f"Permission Error: Permission to access '{e.filename}' was denied.")
        return None
    except shutil.SameFileError as e:
        print(f"File Error: Source and destination represents the same file.")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def display_help_commands():
    for command in COMMANDS:
        print(command[0], (60 - len(command[0])) * " ", command[1])

    print("")


def display_abbreviations():
    with open("abbreviations.json", "r") as f:
        abreviations = json.load(f)
        for key, value in abreviations.items():
            print(f"{key} {(15 - len(key)) * ' '} {value[0]}")


class CLI(cmd.Cmd):

    def preloop(self):
        try:
            delims = readline.get_completer_delims()
            if "-" in delims:
                readline.set_completer_delims(delims.replace("-", ""))
        except Exception:
            pass

    intro = f"""{MAGENTA}
    _____  ___     _____ _______ ______         __  __       _____ __     ______ 
    |  _ \(_) |   / ____|__   __|  ____|   /\   | |/ /      / ____| |    |_   _|
    | |_) |_| |__| (___    | |  | |__     /  \  | ' /      | |    | |      | |  
    |  _ <| | '_ \___ \    | |  |  __|   / /\ \ |  <       | |    | |      | |  
    | |_) | | |_) |___) |  | |  | |____ / ____ \| . \      | |____| |____ _| |_ 
    |____/|_|_.__/_____/   |_|  |______/_/    \_\_|\_\      \_____|______|_____|
    {RESET}                                                                                                                                                                                                                
    Welcome to BibStShell! Type 'help' to list commands.
    The current/last working directory is: '{
    get_working_directory_path() if get_working_directory_path() != "" else "No directory has been set"}'
    If you want to change it use the set_directory <source_directory> command
    and add the absolute path as an argument.
    """
    prompt = f"{MAGENTA}BibSTEAK CLI >:{RESET}"
    completekey = "tab"
    doc_header = "Available commands:"
    undoc_header = "Other commands:"
    misc_header = "Topics:"
    ruler = "-"

    # commands
    def do_load(self, arg):
        load_file_to_storage(arg)

    def do_list(self, arg):
        try:
            folder_path = get_working_directory_path()

            if os.listdir(folder_path):
                files = get_bib_file_names(folder_path)
                if files != []:
                    print(f"Bib files in {folder_path}")
                    for file, index in files:
                        print(f"{BLUE}[{index}] {RESET}", file)
                else:
                    print("No .bib files found in the working directory!")
            else:
                print("The working directory is empty!")

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def do_pwd(self, arg):
        print(
            f"{BLUE}Current working directory: {get_working_directory_path() if get_working_directory_path() != '' else 'No working directory is selected.'}{RESET}"
        )

    def do_cd(self, wd_path):

        try:
            if wd_path == "":
                raise ValueError("No path provided. Please provide an absolute path.")
            if not os.path.exists(wd_path):
                raise FileNotFoundError(f"Path not found: {wd_path}")
            if not os.path.isdir(wd_path):
                raise TypeError(f"The provided path is not a directory: {wd_path}")

            with open("config.json", "r") as f:
                config = json.load(f)

            config["working_directory"] = wd_path

            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)

            print_in_green(f"Directory successfully set to {wd_path}")

        except Exception as e:
            print(f"Path Error: {e}")
            return None

    def do_help(self, arg):
        display_help_commands()

    def do_abb(self, arg):
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
        
    def do_filter(self, args):
        try:
            args_split = args.split()

            #get bibfileobj
            filename = args_split[0]
            path = os.path.join(get_working_directory_path(), filename)
            bibfileobj = utils.file_parser.parse_bib(path, False)
        
            field = args_split[1]

            if len(args_split) == 3:
                value = args_split[2]
                newFile = filterByFieldValue(bibfileobj, field, value)
                if newFile == -1:
                    print_in_yellow(f"No references found with a field named {WHITE}{field}{YELLOW} with value {WHITE}{value}")
                else:
                    self.do_view_bibfile_obj(newFile)
            else:
                newFile = filterByFieldExistence(bibfileobj, field)
                if newFile == -1:
                    print_in_yellow(f"No references found with a field named {WHITE}{field}")
                else:
                    self.do_view_bibfile_obj(newFile)
        except IndexError as e:
            print_in_yellow(f"Index error! Specify arguments: <filename> <field> [OPT: value]")
        except FileNotFoundError as e:
            print_in_yellow(f"File {WHITE}\"{filename}\"{YELLOW} not found! Check your spelling.")
        except Exception as e:
            print_in_yellow(f"Unexpected error: {e}")
                    

    def do_search(self, args):
        
        try:
            filename, searchterm = args.split()
            path = os.path.join(get_working_directory_path(), filename)
            bibfileobj = utils.file_parser.parse_bib(path, False)

            newFile = search(bibfileobj, searchterm)
            if newFile == -1:
                print_in_green("No references match your search :(")
            else: 
                self.do_view_bibfile_obj(newFile)
        except IndexError as e:
            print_in_yellow(f"Index error! Specify two arguments: <filename> <searchterm>")
        except FileNotFoundError as e:
            print_in_yellow(f"File {WHITE}\"{filename}\"{YELLOW} not found! Check your spelling.")
        except Exception as e:
            print_in_yellow(f"Unexpected error: {e}")

    def do_view_bibfile_obj(self, args):
        for item in args.content:
            print(f"{YELLOW}|>  {RESET}", item, end="\n\n")
        

    def do_br(self, args):
        try:
            filename, fields, old_string, new_string = args.split()
            print(filename, fields, old_string, new_string)

            # working_direcory =
            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)

            batch_editor.batch_replace(bib_file, fields, old_string, new_string)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name, 15)

            print_in_green("Batch replace has been done successfully!")

        except Exception as e:
            print(f"Unexpected error: {e}")

    def do_rg(self, args):
        try:
            filename, order = args.split()

            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)

            sortByReftype(bib_file, order)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name, 15)

            print_in_green("Grouping by reference done successfully!")

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def do_exp(self, arg):
        try:
            filename = arg
            if filename == "":
                raise ValueError("No filename provided. Please provide a filename.")

            # working_direcory =
            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)

            abbreviations_exec.execute_abbreviations(bib_file, False, 1000)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name, 15)

            print_in_green("Expanding abbreviations has been done successfully!")

        except ValueError as e:
            print(f"Argument error: {e}")
            return None
        except FileNotFoundError as e:
            print(f"File error: {e.filename} not found.")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def do_col(self, arg):
        try:
            filename = arg
            if filename == "":
                raise ValueError("No filename provided. Please provide a filename.")

            # working_direcory =
            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)

            abbreviations_exec.execute_abbreviations(bib_file, True, 1000)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name, 15)

            print_in_green("Collapsing abbreviations has been done successfully!")

        except ValueError as e:
            print(f"Argument error: {e}")
            return None
        except FileNotFoundError as e:
            print(f"File error: {e.filename} not found.")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def do_sub(self, args):
        try:
            argument_list = args.split(maxsplit=3)
            flag, filename, new_filename = argument_list[:3]
            search_list = argument_list[3:][0]
            path = os.path.join(get_working_directory_path(), filename)
            new_filename = check_extension(new_filename)
            file = utils.file_parser.parse_bib(path, True)
            match flag:
                case "-e":
                    entry_types_list = ast.literal_eval(search_list)
                    sub_file = sub_bib_entry_types(file, entry_types_list)
                case "-t":
                    tags = ast.literal_eval(search_list)
                    sub_file = sub_bib_tags(file, tags)
                case _:
                    print("Flag not supported!")
                    return

            new_path = os.path.join(get_working_directory_path(), new_filename)
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            utils.file_generator.generate_bib(sub_file, new_path, 15)
            print_in_green("Sub operation done successfully!")

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def do_ord(self, args):
        try:

            def str_to_bool(s: str) -> bool:
                return s.strip().lower() in ("True", "true", "1", "yes", "y", "on")

            args_split = args.split()
            filename = args_split[0]
            field = args_split[1]
            if len(args_split) == 3:
                descending = str_to_bool(args_split[2])
            else:
                descending = False

            # print(type(entry_types))
            path = os.path.join(get_working_directory_path(), filename)
            file = utils.file_parser.parse_bib(path, True)
            order_by_field(file, field, descending)
            utils.file_generator.generate_bib(path, file, 15)

            if descending == False:
                print_in_green(f"Ascending order by '{field}' field done successfully!")
            else:
                print_in_green(
                    f"Descending order by '{field}' field done successfully!"
                )

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def do_mer(self, args):
        try:
            argument_list = args.split()
            if len(argument_list) == 2 and argument_list[0] == "-all":
                new_file_name = argument_list[1]
                new_file_name = check_extension(new_file_name)
                wd = get_working_directory_path()
                if not os.listdir(wd):
                    print("The working directory is empty!")
                    return
                file_names = get_bib_file_names(wd)
                path = os.path.join(get_working_directory_path(), file_names[0][0])
                merged_bib_file = utils.file_parser.parse_bib(path, False)
                for file_name, index in file_names:
                    if index == 1:
                        continue
                    path = os.path.join(get_working_directory_path(), file_name)
                    bib_file = utils.file_parser.parse_bib(path, False)
                    merged_bib_file = merge.merge_files(merged_bib_file, bib_file)
                utils.file_generator.generate_bib(merged_bib_file, new_file_name, 15)

            else:
                file_name_1, file_name_2, new_file_name = args.split()
                new_file_name = check_extension(new_file_name)

                path_1 = os.path.join(get_working_directory_path(), file_name_1)
                path_2 = os.path.join(get_working_directory_path(), file_name_2)
                bib_file_1 = utils.file_parser.parse_bib(path_1, False)
                bib_file_2 = utils.file_parser.parse_bib(path_2, False)

                merge_result = merge.merge_files(bib_file_1, bib_file_2)
                utils.file_generator.generate_bib(merge_result, new_file_name, 15)

            print_in_green("Files have been merged successfully!")

        except ValueError as e:
            if "not enough values to unpack" in str(e):
                print(
                    "Argument error: Not enough arguments provided. Please provide three arguments: <filename1> "
                    "<filename2> <new_filename>."
                )
            else:
                print(f"Argument error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    def default(self, line):
        print("Command not found!")

    def emptyline(self):
        pass

    def filename_completions(self, text):
        wd = get_working_directory_path()
        try:
            return [
                f for f in os.listdir(wd) if f.endswith(".bib") and f.startswith(text)
            ]
        except Exception:
            return []

    def complete_view(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_filter(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_search(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_exp(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_rg(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_br(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_ord(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_sub(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_col(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_load(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_mer(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    # Add similar methods for other commands that take filenames as arguments


if __name__ == "__main__":
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    CLI().cmdloop()
