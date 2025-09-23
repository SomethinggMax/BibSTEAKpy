
from typing import List, Union, Set

class File(object):
    def __init__(self, filename):
        self.references = list()
        self.filename = filename
        
    def get_number(self):
        return self.filename
    
    def append_reference(self, reference):
        self.references.append(reference)
        
    def get_references(self):
        return self.references
    
    def __str__(self):
        return f"[File: {self.filename} - refs: {self.references}]"
    
    def __repr__(self):
        return self.__str__()
    

class Reference(object):
    def __init__(self, entry_type, citekey):
        self.entry_type = entry_type
        self.citekey = citekey
        self.author = None
        
    def get_key(self):
        return (self.entry_type, self.citekey)
    
    def __str__(self):
        return f"[Reference: {self.get_key()} author:{self.author}]"
    
    def __repr__(self):
        return self.__str__()
    
    def get_non_none_fields(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}
        
    
if __name__ == "__main__":
    object = File("random_file.bib")
    reference = Reference("article", "au32")
    reference.author = "George"
    
    # You can add custom attributes to the object dynamically
    # even thought the object has already been instantiated
    reference.year = 2004
    reference.custom_attribute = "custom value"
    print(reference.custom_attribute)
    object.append_reference(reference)
    print(object.get_references())