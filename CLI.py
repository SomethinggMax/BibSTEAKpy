import cmd
import os
import shutil
import readline
from utils import merge, cleanup, enrichment
import utils.file_generator as file_generator
import utils.abbreviations_exec as abbreviations_exec
import utils
from utils.sub_bib import *
from utils.Reftype import *
from utils.abbreviations_exec import *
from utils.filtering import *
import ast
import graph
from graph import generate_graph
from history_manager import (
    commit,
    redo,
    undo,
    initialise_history,
    checkout,
    history,
    delete_history,
    comment
)

if os.name == "nt" and not hasattr(readline, "backend"):
    readline.backend = "unsupported"

RESET = "\033[0m"
RST = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
M = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"


def print_in_green(arg):
    print(f"{GREEN}{arg}{RESET}")


def print_in_yellow(arg):
    print(f"{YELLOW}{arg}{RESET}")

def print_error_msg(error_type: Exception, msg):
    error_type = error_type.__class__.__name__
    match error_type:
        case "ValueError" | "IndexError":
            print_in_yellow(f"The command should be invoked as follows: {GREEN}{msg}")
        case "FileNotFoundError":
            print_in_yellow(f"Path to {CYAN}'{msg}'{YELLOW} not found! Check your spelling")
        case "PermissionError":
            print_in_yellow(f"Permission to access {CYAN}'{msg}'{YELLOW} was denied")
        case "Exception":
            print_in_yellow(f"{RED}Unexpected error: {YELLOW}{msg}")
        case _:
            print_in_yellow(f"{RED}{error_type}: {YELLOW}{msg}")


CONFIG_FILE = "config.json"
TAGS_FILE = "tags.json"  # TODO

COMMANDS = {
    f"{MAGENTA}BASE COMMANDS{RESET}" : [
        ("help", "Display the current menu"),
        (
            "load <absolute/path/to/file>",
            "Load a particular file into the working directory",
        ),
        ("cwd <absolute/path/to/directory>", "Changes/Adds the working directory"),
        ("list", "Lists all the bib files in the current working directory"),
        ("pwd", "Prints the current working directory"),
        ("abb", "Display the abbreviations legend"),
        (
            "view <filename>",
            "View the content of a certain .bib file from your current working directory",
        ),
        ("quit", "Close the BibSteak CLI"),
    ],
    
    f"{MAGENTA}FUNCTIONAL COMMANDS{RESET}": [
        ("exp <filename>", "Expand all abbreviations in the file"),
        ("col <filename>", "Collapse all abbreviations in the file"),
        (
            "br <filename> <old string> <new string> [fieldslist=None]",
            "Replace all occurrences in given fields (OPTIONAL: a list of fields in which to search)",
        ),
        ("clean <filename>", "Cleans file according to rules in config."),
        (
            "sub -e <filename> <new filename> <entrytypes list>",
            "Creates a sub .bib file with only specified entry " "types.",
        ),
        (
            "sub -t <filename> <new filename> <tags list>",
            "Creates a sub .bib file with only references with specified " "tags.",
        ),
        ("tag <tag> <query>", "Adds a tag to all the references that return from a query. A query can either be a filter or search command"),
        ("tag -ls", "Lists all added tags"),
        (
            "mer <filename1> <filename2> <new_filename>",
            "Merge the references from two bib files into one file.",
        ),
        (
            "mer -all <new_filename>",
            "Merge all bib files in the current working directory.",
        ),
        ("graph [k_regular=2]", "Generates a directed K-regular graph of a bib file"),
        (
            "search <filename> <searchterm>",
            "Displays references with a certain searchterm",
        ),
        (
            "filter <filename> <field> [value=None]",
            "Displays references with a certain field (OPTIONAL: a value in that field)",
        ),
        ("enr <filename>", "Enriches a bibfile by getting information from the web"), #TODO: better description
    ],
    
    f"{MAGENTA}VERSION CONTROL COMMANDS{RESET}": [
        ("undo <filename>", "Undo one step - Jump to the preceeding commmit"),
        ("redo <filename>", "Redo one step - Jump to the suceeding commmit"),
        ("checkout <filename> <commit_hash>", "Checkout to a historic version of the file indexed by the commit_hash"),
        ("del <filename>", "Delete all the history logs for a file"),
        ("history <filename>", "Show the historic commit graph"),
        ("comment <filename> <commit_hash> <comment>", "Add a comment to a specific commit"),    
    ]
    
}

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


def display_help_commands(space_length = 60, indent = 0):
    print("")
    
    for category, commands in COMMANDS.items():
        print(f"{MAGENTA}{category}{RESET}")
        ordered_commands = sorted(commands, key=lambda command: command[0])
        for command in ordered_commands:
            print(f"{BLUE}> {RESET}", command[0], (space_length - len(command[0])) * " ", command[1])

def path_to_bibfileobj(filename):
    path = os.path.join(get_working_directory_path(), filename)
    bibfileobj = utils.file_parser.parse_bib(path, False)
    return bibfileobj

class CLI(cmd.Cmd):

    def preloop(self):
        try:
            delims = readline.get_completer_delims()
            if "-" in delims:
                readline.set_completer_delims(delims.replace("-", ""))
        except Exception:
            pass

    intro = f"""{MAGENTA}
    _____    __     ____________ ______         __  __       _______      ______ 
    |    \(_) |   / ____|__   __|  ____|   /\   | |/ /      / ____| |    |_   _|
    | |_) |_| |_ | (___    | |  | |__     /  \  | ' /      | |    | |      | |  
    |    <| |  _ \___  \   | |  |  __|   / /\ \ |  <       | |    | |      | |  
    | |_) | | |_) |___) |  | |  | |____ / ____ \| . \      | |____| |____ _| |_ 
    |____/|_|_.__/_____/   |_|  |______/_/    \_\_|\_\      \_____|______|_____|
    {RESET}                                                                                                                                                                                                                
    Welcome to BibStShell! Type 'help' to list commands.
    The current/last working directory is {CYAN}'{
    get_working_directory_path() if get_working_directory_path() != "" else "No directory has been set"}'{RESET}
    """
    prompt = f"{MAGENTA}BibSTEAK CLI >:{RESET}"
    completekey = "tab"
    doc_header = "Available commands:"
    undoc_header = "Other commands:"
    misc_header = "Topics:"
    ruler = "-"

    # commands
    def do_load(self, arg):
        """
        Copy a file from source_path into the storage folder.
        Creates the folder if it doesn't exist.
        """
        try:

            if arg == "":
                raise ValueError(f"The command should be invoked as follows: {GREEN}load <absolute/path/to/file>")

            working_directory = get_working_directory_path()
            if working_directory == "":
                raise Exception(f"no working directory is selected. Use {GREEN}cwd <absolute/path/to/directory>")
     
            filename = os.path.basename(arg)
            name, extension = os.path.splitext(filename)
            destination_path = os.path.join(working_directory, filename)

            if extension != ".bib":
                if extension == "":
                    raise ValueError("File has no extension! Only .bib files are allowed.")
                else:
                    raise ValueError(f"Invalid file extension: {RED}{extension}{YELLOW}! Only .bib files are allowed.")

            shutil.copy(arg, destination_path)
            print_in_green(f"File {CYAN}'{filename}'{GREEN} loaded into the storage successfully!")

        except ValueError as e:
            #NOTE! This should not be changed to print_error_msg, since the custom messages are important
            print_in_yellow(f"{e}") 
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except shutil.SameFileError as e:
            print_error_msg(e,e)
        except OSError as e:
            print_error_msg(e,e)
        except Exception as e:
            print_error_msg(e,e)

    def do_list(self, arg):
        try:
            folder_path = get_working_directory_path()
            if folder_path == "":
                raise Exception(f"no working directory is selected. Use {GREEN}cwd <absolute/path/to/directory>")

            if os.listdir(folder_path):
                files = get_bib_file_names(folder_path)
                if files != []:
                    # print(f"{BLUE}Bib files in {folder_path}:")
                    for file, index in files:
                        print(f"{BLUE}[{index}] {RESET}", file)
                else:
                    print("No .bib files found in the working directory!")
            else:
                print("The working directory is empty!")
        except Exception as e:
            print_error_msg(e,e)

    def do_pwd(self, arg):
        if get_working_directory_path() != "":
            print(f"The current working directory is {CYAN}'{get_working_directory_path()}'")
        else:
            print_in_yellow("No working directory is selected")

    def do_cwd(self, args):
        try:
            wd_path = args.split()[0]

            if not os.path.exists(wd_path):
                raise FileNotFoundError()
            if not os.path.isdir(wd_path):
                raise TypeError(f"the provided path is not a directory: {wd_path}")

            with open("config.json", "r") as f:
                config = json.load(f)

            config["working_directory"] = wd_path

            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)

            print_in_green(f"Directory successfully set to {CYAN}'{wd_path}'")

        except (ValueError, IndexError) as e:
            print_error_msg(e, "cwd <absolute/path/to/directory>")
        except FileNotFoundError as e:
            print_error_msg(e, e.filename)
        except (TypeError, Exception) as e:
            print_error_msg(e, e)

    def do_cd(self, wd_path):
        self.do_cwd(wd_path)
        return

    def do_help(self, arg):
        display_help_commands()

    def do_abb(self, arg):
        with open("abbreviations.json", "r") as f:
            abreviations = json.load(f)
            for key, value in abreviations.items():
                print(f"{key} {(15 - len(key)) * ' '} {value[0]}")

    def do_quit(self, arg):

        try:
            ui.shutdown()  # stops uvicorn
        except Exception:
            pass

        print(f"{GREEN}Bye! - Shell closed{RESET}")

        return True  # returning True exits the loop

    # TODO: pretty up?
    # TODO: store all files as preprocessed bibfiles in this cli?
    def do_view(self, arg):
        try:
            path = os.path.join(get_working_directory_path(), arg)
            with open(path, "r") as f:
                for line in f:
                    print(f"", line, end="")
            print("\n")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print_error_msg(e,e)

    def do_filter(self, args):
        try:
            args_split = args.split()

            # get bibfileobj
            filename = args_split[0]
            bibfileobj = path_to_bibfileobj(filename)

            field = args_split[1]

            if len(args_split) == 3:
                value = args_split[2].lower()
                array = filterByFieldValue(bibfileobj, field, value)

                if array == -1:
                    print_in_yellow(f"No references found with a field named {CYAN}'{field}'{YELLOW} with value {CYAN}'{value}'")
                    return
                self.do_view_array(array)
            else:
                array = filterByFieldExistence(bibfileobj, field)
                if array == -1:
                    print_in_yellow(f"No references found with a field named {CYAN}'{field}'")
                    return
                self.do_view_array(array)
        except (ValueError, IndexError) as e:
            print_error_msg(e, "filter <filename> <field> [value=None]")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print_error_msg(e,e)

    def do_search(self, args):
        try:
            filename, searchterm = args.split()
            bibfileobj = path_to_bibfileobj(filename)

            array = search(bibfileobj, searchterm)
            if array == -1:
                print_in_yellow(f"No instances of {CYAN}'{searchterm}'{YELLOW} found in {CYAN}'{filename}'") #TODO: diff colour?
                return
            
            self.do_view_array(array)
        except (IndexError, ValueError) as e: 
            print_error_msg(e, "search <filename> <searchterm>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print_error_msg(e,e)

    def do_view_array(self, args):
        for item in args:
            print(f"{YELLOW}|>  {RESET}", item, end="\n\n")

    def do_br(self, args):
        try:
            arguments = args.split()

            if len(arguments) == 3:
                filename, old_string, new_string = args.split()
                fields = []
            elif len(arguments) == 4:
                filename, old_string, new_string, fields = args.split()
            else:
                raise ValueError()

            #get and save history of file
            bib_file = path_to_bibfileobj(filename)
            initialise_history(bib_file)

            #do batch replace
            bib_file = batch_editor.batch_replace(bib_file, fields, old_string, new_string)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name)
            commit(bib_file)

            print_in_green("Batch replace has been done successfully!")

        except ValueError as e:
            print_error_msg(e, "br <filename> <old string> <new string> [fieldslist=None]")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print_error_msg(e,e)

    def do_ord(self, args):
        try:
            arguments = args.split()

            if len(arguments) > 1:
                filename, order = arguments[0], arguments[1]
                order = (
                    GroupingType.ZTOA
                    if order in ["True", "true", "1", "Yes", "yes"]
                    else GroupingType.ATOZ
                )
            else:
                filename = arguments[0]
                order = GroupingType.ATOZ

            bib_file = path_to_bibfileobj(filename)

            initialise_history(bib_file)
            sortByReftype(bib_file, order)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name)
            commit(bib_file)

            print_in_green(
                f"Grouping by reference done successfully in {order.name} order"
            )

        except IndexError as e:
            print(f"Unexpected error: {e}")
            return
        except Exception as e:
            print(f"Unexpected error: {e}")
            return

    def do_exp(self, arg):
        try:
            filename = arg
            if filename == "":
                raise ValueError()

            # working_direcory =
            bib_file = path_to_bibfileobj(filename)

            initialise_history(bib_file)
            abbreviations_exec.execute_abbreviations(bib_file, False, 1000)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name)
            commit(bib_file)

            print_in_green("Expanding abbreviations has been done successfully!")

        except ValueError as e:
            print_error_msg(e, "exp <filename>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print(f"Unexpected error: {e}")

    def do_col(self, arg):
        try:
            filename = arg
            if filename == "":
                raise ValueError()

            bib_file = path_to_bibfileobj(filename)

            initialise_history(bib_file)
            abbreviations_exec.execute_abbreviations(bib_file, True, 1000)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name)
            commit(bib_file)

            print_in_green("Collapsing abbreviations has been done successfully!")

        except ValueError as e:
            print_error_msg(e, "col <filename>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print(f"Unexpected error: {e}")

    def do_tag(self, args):
        try:
            arguments = args.split()
            flag = arguments[0]

            if flag == "-ls":
                with open("tags.json") as tagsfile:
                        tags = json.load(tagsfile)
                        for key, value in tags.items():  # TODO: if empty
                            print(f"{YELLOW}{key} {RESET}{value}")  # TODO: pretty
            else:
                tag = arguments[0]
                query = arguments[1:]
                query_type = query[0]
                filename = query[1]
                bibfileobj = path_to_bibfileobj(filename)
                term = query[2]
                array = []

                match query_type:
                    case "search":
                        array = search(bibfileobj, term)
                    case "filter":
                        if len(query) == 3:
                            array = filterByFieldExistence(bibfileobj, term)
                        elif len(query) == 4:
                            array = filterByFieldValue(bibfileobj, term, query[3])
                    case _:
                        print_in_yellow(f"Invalid query! A query can either look like...\n{GREEN}search <filename> <searchterm>\nfilter <filename> <field> [OPT=value]")
                        return

                # no queries returned, tell the user
                if array == -1:
                    print_in_yellow("Query returns no matches! No tags have been added")
                    return

                #get cite_keys only
                newarr = [ref.cite_key for ref in array]
                with open("tags.json", "r+") as tagsfile:
                    # add the new tagged references
                    tags = json.load(tagsfile)
                    if tag in tags.keys():
                        tags[tag] += newarr  # TODO: duplicates
                    else:
                        tags[tag] = newarr

                    tagsfile.seek(0)  # go to beginning of file
                    json.dump(tags, tagsfile, indent=4)  # replace content
                print_in_green("Successfully added tags!")

        except (ValueError, IndexError) as e:
            print_error_msg(e, f"\ntag <tag> <query> {YELLOW}where {GREEN}<query>{YELLOW} is a search or filter command{GREEN}\ntag -ls")
        except FileNotFoundError as e:
            if e.filename == "tags.json":
                print_in_yellow("Tags file not found! Creating \"tags.json\" for you...") #TODO
                with open("tags.json", "w+") as tagsfile:
                    json.dump({}, tagsfile)
                print_in_green("Try and run the command again")
            else:
                print_error_msg(e,e.filename)
        except Exception as e:
            print_error_msg(e,e)

    # TODO
    def do_untag(self, args):
        try:
            arguments = args.split()
            flag = arguments[0]

            match flag:
                case "-q":
                    tag = arguments[1]
                    query = arguments[2:]
                    array = []


                    bibfileobj = path_to_bibfileobj(query[1])

                    match query[0]:
                        case "search":
                            array = search(bibfileobj, query[2])
                        case "filter":
                            if len(query) == 3:
                                array = filterByFieldExistence(bibfileobj, query[2])
                            elif len(query) == 4:
                                array = filterByFieldValue(
                                    bibfileobj, query[2], query[3]
                                )
                            else:
                                print("Invalid query given!")
                                return
                        case _:
                            print_in_yellow("Invalid query! Check your spelling")
                            return

                    # no queries returned, tell the user
                    if array == -1:
                        print("Query returns no matches! No tags have been added")
                        print("Query returns no matches! No tags have been added")
                        return

                    #get cite_keys only
                    newarr = [ref.cite_key for ref in array]
                    with open("tags.json", "r+") as tagsfile:
                        # remove tags
                        tags = json.load(tagsfile)
                        if tag in tags.keys():
                            for citekey in tags[tag]:
                                if citekey in newarr:
                                    newarr.remove(citekey)
                        else:
                            print_in_yellow("Tag not found in the tags file. Check your spelling.")
                            return

                        # TODO: remove fully empty tags
                        tags[tag] = newarr

                        tagsfile.seek(0) #go to beginning of file
                        tagsfile.truncate(0)
                        json.dump(tags, tagsfile, indent=4)  # replace content
                    print_in_green("Successfully removed tags!")
                    return
                case "-ls":
                    tag = arguments[1]
                    citekeylist = arguments[2]

                    tags = json.load(tagsfile)
                    if tag in tags.keys():
                        for citekey in tags[tag]:
                            if citekey in citekeylist:
                              #TODO: remove tag
                              return
                    else:
                        print_in_yellow("Tag not found in the tags file. Check your spelling.")
                        return
                    return
                case _:
                    print("Flag not supported!")
                    return
        except IndexError as e:
            print_in_yellow(
                f"Command is not complete, please check the amount of arguments.\nThe command can be invoked in two ways:\nuntag -q <tag> <query> where <query> is a search or filter command\nuntag -ls <tag> <citekey list>"
            )
            return
        # except FileNotFoundError as e: #TODO
        #     print_in_yellow("Tags file not found! Creating \"tags.json\" for you...") #TODO
        #     with open("tags.json", "w+") as tagsfile:
        #         json.dump({}, tagsfile)
        #     print_in_green("Try and run the command again")
        except Exception as e:
            print_in_yellow(f"Unexpected error: {e}")

    """
    Makes a sub .bib file from a selected list of entry types or tags
    """

    def do_sub(self, args):
        try:
            arguments = args.split()

            flag = arguments[0]
            if not flag.startswith("-"):
                raise ValueError("Flag not supported!")
                
            filename = arguments[1]
            file = path_to_bibfileobj(filename)

            new_filename = arguments[2]
            new_filename = check_extension(new_filename)

            search_list = arguments[3:][0] #TODO: PARSING

            match flag:
                case "-e":
                    entry_types_list = ast.literal_eval(search_list) #TODO: PARSING AND MALFORMED THING WHEN LIST INCORRECTLY PASSED
                    sub_file = filter_entry_types(file, entry_types_list)
                case "-t":
                    tags = ast.literal_eval(search_list) #TODO: PARSING AND MALFORMED THING WHEN LIST INCORRECTLY PASSED
                    sub_file = filter_tags(file, tags)
                case _:
                    raise ValueError("Flag not supported!")

            new_path = os.path.join(get_working_directory_path(), new_filename)
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            utils.file_generator.generate_bib(sub_file, new_path)
            print_in_green("Sub operation done successfully!")

        except (ValueError, IndexError) as e:
            print_error_msg(e, f"sub -e <filename> <new filename> <entrytypes list>\nsub -t <filename> <new filename> <tags list> \n{YELLOW}Where the lists are structured like [\"item1\", \"item2\", ...]")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print_error_msg(e,e)

    def do_clean(self, arg):
        try:
            filename = arg
            if filename == "":
                raise ValueError()

            # working_direcory =
            bib_file = path_to_bibfileobj(filename)

            initialise_history(bib_file)
            cleanup.cleanup(bib_file)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name)
            commit(bib_file)

            print_in_green("Cleanup has been done successfully!")

        except ValueError as e:
            print_error_msg(e, "clean <filename>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print(f"Unexpected error: {e}")

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
                merged_bib_file = path_to_bibfileobj(file_names[0][0])
                for file_name, index in file_names:
                    if index == 1:
                        continue
                    bib_file = path_to_bibfileobj(file_name)
                    merged_bib_file = merge.merge_files(merged_bib_file, bib_file)
                # Write output inside the configured working directory
                out_path = os.path.join(get_working_directory_path(), new_file_name)
                utils.file_generator.generate_bib(merged_bib_file, out_path)

            else:
                file_name_1, file_name_2, new_file_name = args.split()
                new_file_name = check_extension(new_file_name)


                bib_file_1 = path_to_bibfileobj(file_name_1)
                bib_file_2 = path_to_bibfileobj(file_name_2)

                merge_result = merge.merge_files(bib_file_1, bib_file_2)

                #TODO: check if overriding file?

                # Write output inside the configured working directory
                out_path = os.path.join(get_working_directory_path(), new_file_name)
                utils.file_generator.generate_bib(merge_result, out_path)

            print_in_green("Files have been merged successfully!")

        except ValueError as e:
            print_in_yellow(f"{RED}ARGUMENT ERROR: {YELLOW}This command should be invoked as follows... \n{GREEN}mer <filename1> <filename2> <new_filename>") #TODO: standardize
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print(f"Unexpected error: {e}")

    def do_graph(self, args):

        try:
            if args:
                if len(args.split()) > 1:
                    raise ValueError("This command only takes one argument!")
                k_regular = int(args)
            else:
                k_regular = 2

            if get_working_directory_path() == "":
                raise ValueError("Working directory not set! Use the cwd command")
            else:
                print(
                    f"{BLUE}PLEASE CHOOSE A FILE FOR GRAPH GENERATION{RESET}"
                )
                self.do_list("")

                index_str = input(f"{BLUE}Enter file index: {RESET}")

                files = get_bib_file_names(
                    get_working_directory_path()
                )  # Check if index is in range
                index = int(index_str)
                print(f"You selected {CYAN}'{files[index-1][0]}'{RESET}")
                file = files[index - 1]
                file_name = file[0]
                bibfileobj = path_to_bibfileobj(file_name)
                graph.generate_graph(bibfileobj, k_regular)

        except KeyboardInterrupt as e:
            print_in_yellow(f"{RED}ABORTED")
        except ValueError as e:
            print_in_yellow(f"{RED}Argument error:{YELLOW} {e}")
        except Exception as e:
            print_in_yellow(f"Unexpected error: {e}")


    def do_undo(self, args):
        try:
            argument_list = args.split()

            if len(argument_list) < 1:
                raise ValueError()
            elif len(argument_list) == 1:
                filename = args
                step = 1
            elif len(argument_list) == 2:
                filename = argument_list[0]
                step = int(argument_list[1])


            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)
            undo(bib_file, step)

        except (ValueError, IndexError) as e:
            print_in_yellow(f"{RED}Argument Error!{YELLOW} The command should be invoked as follows...\n{GREEN}undo <filename>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print_in_yellow(f"Unexpected error: {e}")

    def do_redo(self, args):
        try:
            argument_list = args.split()

            if len(argument_list) < 1:
                raise ValueError()
            elif len(argument_list) == 1:
                filename = args
                step = 1
            elif len(argument_list) == 2:
                filename = argument_list[0]
                step = int(argument_list[1])


            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)
            redo(bib_file, step)


        except (ValueError, IndexError) as e:
            print_in_yellow(f"{RED}Argument Error!{YELLOW} The command should be invoked as follows...\n{GREEN}redo <filename>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print_in_yellow(f"{RED}Unexpected error:{YELLOW} {e}")

    def do_checkout(self, args):
        try:
            argument_list = args.split()
            if len(argument_list) == 2:
                filename = argument_list[0]
                commit_hash = argument_list[1]
            else:
                raise IndexError()
            
            if not os.path.isfile(os.path.join(get_working_directory_path(), filename)):
                print_in_yellow(f"{filename} doesn't exist in {get_working_directory_path()}")
                return
            
            hist_dir_path = os.path.join("history", f"hist_{filename}")
            checkout_path = os.path.join(hist_dir_path, commit_hash)
            
            if not os.path.isfile(checkout_path):
                print_in_yellow(f"Commit hash for file {filename} is not valid")
                return
                
            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)
            checkout(bib_file, commit_hash)
            print_in_green(f"Checkout done successfully to commit: {commit_hash}")

        except (ValueError, IndexError) as e:
            print_in_yellow(f"{RED}Argument Error!{YELLOW} The command should be invoked as follows...\n{GREEN}checkout <filename> <commit_hash>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
                print(f"Unexpected error: {e}")
            
    def do_comment(self, args):
        try:
            argument_list = args.split(maxsplit = 2)
            if len(argument_list) == 3:
                filename = argument_list[0]
                commit_hash = argument_list[1]
                checkout_comment = argument_list[2]
            else:
                print_in_yellow("Not enough arguments!")
                return
            
            if not os.path.isfile(os.path.join(get_working_directory_path(), filename)):
                print_in_yellow(f"{filename} doesn't exist in {get_working_directory_path()}")
                return
            
            hist_dir_path = os.path.join("history", f"hist_{filename}")
            checkout_path = os.path.join(hist_dir_path, commit_hash)
            
            if not os.path.isfile(checkout_path):
                print_in_yellow(f"Commit hash for file {filename} is not valid")
                return
                
            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)
            comment(bib_file, commit_hash, checkout_comment)
            print_in_green(f"Commenting done successfuly")
            
        except (ValueError, IndexError) as e:
            print_in_yellow(f"{RED}Argument Error!{YELLOW} The command should be invoked as follows...\n{GREEN}comment <filename> <commit_hash> <comment>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
                print(f"Unexpected error: {e}")
        
            
    def do_history(self, args):
        try:
            filename = args
            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)
            
            history(bib_file)
        except (ValueError, IndexError) as e:
            print_in_yellow(f"{RED}Argument Error!{YELLOW} The command should be invoked as follows...\n{GREEN}history <filename>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print(f"Unexpected error: {e}")

    def do_del(self, args):
        try:
            filename = args
            if filename == "":
                raise ValueError()

            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)
            delete_history(bib_file)
            print_in_green(f"History of {CYAN}'{filename}'{GREEN} deleted successfuly!")

        except (ValueError, IndexError) as e:
            print_error_msg(e, "del <filename>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
                print(f"Unexpected error: {e}")

    def do_enr(self, arg):
        try:
            filename = arg
            if filename == "":
                raise ValueError()

            bib_file = path_to_bibfileobj(filename)
            utils.enrichment.sanitize_bib_file(bib_file)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name)
            commit(bib_file)

            print_in_green("Enrichment has been done successfully!")

        except (ValueError, IndexError) as e:
            print_error_msg(e,"enr <filename>")
        except (FileNotFoundError, PermissionError) as e:
            print_error_msg(e, e.filename)
        except Exception as e:
            print_error_msg(e,e)

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

    def complete_gr(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_br(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_ord(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_clean(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_sub(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_col(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_load(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_mer(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_enr(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    # Add similar methods for other commands that take filenames as arguments

if __name__ == "__main__":
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    try:
        CLI().cmdloop()
    except KeyboardInterrupt as e:
        print(f"{GREEN}An interruption has occured! - Shell closed{RESET}")
