import cmd
import os
import shutil
import json
import readline
from nicegui import ui, app
import networkx as nx
# pip install pywebview

if os.name == 'nt' and not hasattr(readline, 'backend'):
    readline.backend = 'unsupported'
import utils.batch_editor as batch_editor
import utils.file_generator as file_generator
from pprint import pprint
from utils.GroupByRefType import groupByRefType
import utils.abbreviations_exec as abbreviations_exec
import utils
from utils.order_by_field import *
from utils.sub_bib import *
from utils.file_parser import *
from utils.file_generator import *
from utils.GroupByRefType import *
from utils.order_by_field import *
from utils.batch_editor import *
from utils.abbreviations_exec import *
import ast
from graph import generate_graph

GREEN = "\033[92m"
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


CONFIG_FILE = "config.json"

COMMANDS = [("help", "Display the current menu"),
            ("load", "Load a particular file into the working directory"),
            ("set_directory <absolte/path/to/wd>", "Choose the ABSOLUTE path to a working directory"),
            ("list", "See all the bib files in the working directory"),
            ("wd", "Get current working directory"),
            ("abbreviations", "Display all abbreviations"),
            ("view <filename>", "View the content of a certain .bib file from your chosen working directory"),
            ("quit", "Close the BibSteak CLI"),
            ("refgroup <filename> <order>", "Group and order based on entry type"),
            ("expand <filename>", "Expand all abbreviations in the file"),
            ("collapse <filename>", "Collapse all abbreviations in the file"),
            ("batch_replace <filename> <fields> <old string> <new string>", "Replace all occurrences in given fields"),
            ("order <filename> <field> [descending=False]", "Sorts the references by a given field. By default is ASC"),
            ("sub <filename> <fields> <old string> <new string>", "TBA"),

            ]


def completer(text, state):
    line = readline.get_line_buffer()
    split_line = line.strip().split()
    if len(split_line) <= 1:
        options = [cmd[0] for cmd in COMMANDS if cmd[0].startswith(text)]
    else:
        try:
            wd = get_working_directory_path()
            files = [f for f in os.listdir(wd) if f.endswith('.bib') and f.startswith(text)]
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
                raise ValueError(f"Invalid file extension: '{extension}'. Only .bib files are allowed.")

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
                index = 1
                files = []
                for filename in os.listdir(folder_path):
                    full_path = os.path.join(folder_path, filename)
                    _, extension = os.path.splitext(filename)
                    if os.path.isfile(full_path) and extension == '.bib':
                        files.append((filename, index))  # ignore subfolders
                        index += 1
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

    def do_wd(self, arg):
        print(f"{BLUE}Current working directory: {get_working_directory_path()}{RESET}")

    def do_set_directory(self, wd_path):

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

    def do_abbreviations(self, arg):
        display_abbreviations()

    def do_quit(self, arg):
        
        try:
            ui.shutdown()          # stops uvicorn
        except Exception:
            pass
        
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
            bib_file = utils.file_parser.parse_bib(path, False)

            batch_editor.batch_replace(bib_file, fields, old_string, new_string)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name, 15)

            print_in_green("Batch replace has been done successfully!")

        except Exception as e:
            print(f"Unexpected error: {e}")

    def do_refgroup(self, args):
        try:
            filename, order = args.split()

            path = os.path.join(get_working_directory_path(), filename)
            bib_file = utils.file_parser.parse_bib(path, False)

            groupByRefType(bib_file, order)
            utils.file_generator.generate_bib(bib_file, bib_file.file_name, 15)

            print_in_green("Grouping by reference done successfully!")

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def do_expand(self, arg):
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

    def do_collapse(self, arg):
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
            filename, new_filename, entry_types = args.split()
            entry_types_list = ast.literal_eval(entry_types)
            # print(type(entry_types))
            path = os.path.join(get_working_directory_path(), filename)
            file = utils.file_parser.parse_bib(path, True)
            sub_file = sub_bib(file, entry_types_list)
            # sub_file = sub_bib(file, ['article'])
            # print(sub_file)
            new_path = os.path.join(get_working_directory_path(), new_filename)
            # print(new_path)
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            utils.file_generator.generate_bib(sub_file, new_path, 15)

            print_in_green("Sub operation done successfully!")

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def do_order(self, args):
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
                print_in_green(f"Descending order by '{field}' field done successfully!")



        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        
    # def do_graph(self, arg):
    #     print("something")
    #     # with open(get_working_directory_path, "r"):
        
    #     wd_path = get_working_directory_path()
    #     for filename in os.listdir(wd_path):
    #         file_path = os.path.join(wd_path, filename)
    #         bib_file = utils.file_parser.parse_bib(file_path, True)
    #         for reference in bib_file.content:
    #             print(reference.entry_type)
    #         # print(bib_file.content)
            
            
    def do_graph(self, args):
        import threading
        import networkx as nx
        import json
        from nicegui import ui

        def run_server():
            try:
                G = nx.DiGraph([("(John, 2024)","(Marie et al., 2017)"), 
                                ("(Hamilton, 2024)","(Marie et al., 2017)"), 
                                ("(Hamilton, 2024)","(Arthur et al., 2007)"), 
                                ("(Jacob, 2003)","(Marie et al., 2017)"), 
                                ("(Arthur et al., 2007)","(Yhong et al., 2008)"),
                                ("(Jacob, 2003)","(Arthur et al., 2007)"),
                                ("(John, 2024)","(Hamilton, 2024)"),
                                ("(John, 2024)","(Mosh, 2025)"),
                                ("(Anne et al., 2001)","(Mosh, 2025)")])
                
                nodes = []
                for n in G.nodes():
                    in_degree = G.in_degree(n)
                    out_degree = G.out_degree(n)
                    label = f"{n}\n(cited by: {in_degree}, cites: {out_degree})"
                    nodes.append({"id": str(n), "label": label})

                # nodes = [{"id": str(n), "label": str(n)} for n in G.nodes()]
                # edges = [{"from": str(u), "to": str(v)} for u, v in G.edges()]
                edges = [{"from": u, "to": v, "arrows": "to", "label": str(G[u][v].get('weight', '')), "font": {
                    "color": "red",        # color of the label text
                    # optional extras:
                    "background": "white", # rectangle background behind text
                    "strokeWidth": 3,
                    "strokeColor": "black"
                }} for u, v in G.edges()]
                nodes_json = json.dumps(nodes)
                edges_json = json.dumps(edges)

                @ui.page('/')
                def page():

                    ui.html('<div id="graph" style="width:100%; height:600px; border:1px solid #ccc;"></div>')
                    ui.run_javascript(f"""
                (function () {{
                    function render() {{
                        const container = document.getElementById('graph');
                        const data = {{
                            nodes: new vis.DataSet({nodes_json}),
                            edges: new vis.DataSet({edges_json})
                        }};
                        const options = {{
                            physics: {{ stabilization: false }},
                            interaction: {{ hover: true, dragNodes: true, zoomView: true }},
                            edges: {{length: 200}}
                        }};
                        new vis.Network(container, data, options);
                    }}
                    if (window.vis) {{ render(); }}
                    else {{
                        const s = document.createElement('script');
                        s.src = 'https://unpkg.com/vis-network/standalone/umd/vis-network.min.js';
                        s.onload = render;
                        document.head.appendChild(s);
                    }}
                }})();
                """)

                # ui.run(port=8090, reload=False)          # open http://localhost:8080
                ui.run(native=True, reload=False)  # opens a native window via PyWebView

                # s = socket.socket(); s.bind(('', 0)); port = s.getsockname()[1]; s.close()
                # ui.run(host='127.0.0.1', port=port, reload=False)
                
            except (KeyboardInterrupt, SystemExit):
                pass
        
        try:
            threading.Thread(target=run_server, daemon=True).start()
            # run_server()
        except Exception:
            pass
    
    
    
    
    
        

    def default(self, line):
        print('Command not found!')

    def emptyline(self):
        pass

    def filename_completions(self, text):
        wd = get_working_directory_path()
        try:
            return [f for f in os.listdir(wd) if f.endswith('.bib') and f.startswith(text)]
        except Exception:
            return []

    def complete_view(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_expand(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_refgroup(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_batch_replace(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_order(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_sub(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    def complete_collapse(self, text, line, begidx, endidx):
        return self.filename_completions(text)

    # Add similar methods for other commands that take filenames as arguments


if __name__ == "__main__":
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    CLI().cmdloop()
