from typing import List, Union, Set


class BibFile(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.content = list()

    def __str__(self):
        return f"[File: {self.file_name} - content: {self.content}]"

    def __repr__(self):
        return self.__str__()


class Comment(object):
    def __init__(self, comment):
        self.comment = comment


class String(object):
    def __init__(self, abbreviation, long_form):
        self.abbreviation = abbreviation
        self.long_form = long_form


class Reference(object):
    def __init__(self, entry_type, citekey):
        self.entry_type = entry_type
        self.citekey = citekey

    def get_key(self):
        return self.entry_type, self.citekey

    def get_entry_type(self):
        return self.entry_type

    def get_non_none_fields(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def __str__(self):
        return f"[Reference: {self.get_key()}]"

    def __repr__(self):
        return self.__str__()


# We will explore these child objects in the future if 
# we have to distinguish between bib entries

class BibTexReference(Reference):
    def __init__(self):
        super().__init__()


class BibLaTexReference(Reference):
    def __init__(self):
        super().__init__()


# JUST FOR TESTING PURPOSES
if __name__ == "__main__":
    random_file = BibFile("random_file.bib")
    example_reference = Reference("article", "au32")
    example_reference.author = "George"

    # You can add custom attributes to the object dynamically
    # even thought the object has already been instantiated
    example_reference.year = 2004
    example_reference.custom_attribute = "custom value"
    print(example_reference.custom_attribute)
    random_file.content.append(example_reference)
    print(random_file.content)
