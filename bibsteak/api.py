
import utils
import os
from utils.Reftype import GroupingType
from utils import file_parser, file_generator, Reftype, order_by_field, filtering






class API(object):
    def __init__(self):
        wd_path = None
        
    def load(self, path):
        print("loaded ", path)
        
    def set_wd(self, passed_wd_path):
        try:
            if passed_wd_path == "":
                raise ValueError("No path provided. Please provide an absolute path.")
            if not os.path.exists(passed_wd_path):
                raise FileNotFoundError(f"Path not found: {passed_wd_path}")
            if not os.path.isdir(passed_wd_path):
                raise TypeError(f"The provided path is not a directory: {passed_wd_path}")
            
            self.wd_path = passed_wd_path
        except Exception as e:
            print(f"Path Error: {e}")
            
    def get_wd(self):
        return self.wd_path
    
    def list_names(self) -> list:
        """
        Retrieve all file names from the set working directory.

        Returns:
            list[str]: A list with all the file names
        """
        def get_bib_file_names(folder_path):
            files = []
            if os.listdir(folder_path):
                for filename in os.listdir(folder_path):
                    full_path = os.path.join(folder_path, filename)
                    _, extension = os.path.splitext(filename)
                    if os.path.isfile(full_path) and extension == ".bib":
                        files.append(filename)  # ignore subfolders
            return files
        
        try:
            folder_path = self.wd_path

            if os.listdir(folder_path):
                files = get_bib_file_names(folder_path)
                return files
            else:
                print("The working directory is empty!")

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        
    def gr(self, filename, order=False):
        """
        Groups the entries in the file by entry_type.

        Args:
            filename: The name of the target file.
            order: The order of grouping. If set to True, it will be in descending order.
        """
        try:
            order = GroupingType.ZTOA if order is True else GroupingType.ATOZ
            path = os.path.join(self.wd_path, filename)
            bib_file = file_parser.parse_bib(path)

            # # initialise_history(bib_file)
            Reftype.sortByReftype(bib_file, order)
            file_generator.generate_bib(bib_file, bib_file.file_name)
            # # commit(bib_file)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        
    def ord(self, filename, field, descending=False):
        """
        Orders the entries in a file based on a specified field.

        Args:
            filename: The name of the target file.
            field: The field used as a key for sorting
            descending: If True the sorting will be done in descending order
        """
        try:
            path = os.path.join(self.wd_path, filename)
            file = file_parser.parse_bib(path)
            
            # initialise_history(file)
            order_by_field.order_by_field(file, field, descending)
            file_generator.generate_bib(file, path)
            # commit(file)

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
        
    def search(self, filename, searchterm) -> bool:
        """
        Search for a specific term in a file.

        Args:
            filename: The name of the target file.
            searchterm: Target serach term
            
        Returns:
            bool: True if found, otherwise False
    
        """
        try:
            path = os.path.join(self.wd_path, filename)
            bibfileobj = utils.file_parser.parse_bib(path)

            newFile = filtering.search(bibfileobj, searchterm)
            
            if newFile == -1:
                return False
            else:
                return True
            
        except IndexError as e:
            print(f"Index error! Specify two arguments: <filename> <searchterm>")
        except FileNotFoundError as e:
            print(f"File {filename} not found! Check your spelling.")
        except Exception as e:
            print(f"Unexpected error: {e}")