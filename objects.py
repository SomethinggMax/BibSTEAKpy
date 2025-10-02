from typing import List, Union, Set


class BibFile(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.content = list()

    def get_cite_keys(self):
        cite_keys = []
        for entry in self.content:
            if type(entry) is Reference:
                cite_keys.append(entry.cite_key)
        return cite_keys

    def get_reference(self, cite_key):
        for entry in self.content:
            if type(entry) is Reference:
                if entry.cite_key == cite_key:
                    return entry

    def get_strings(self):
        strings = []
        for entry in self.content:
            if type(entry) is String:
                strings.append(entry)
        return strings

    def __str__(self):
        return f"[File: {self.file_name} - content: {self.content}]"

    def __repr__(self):
        return self.__str__()


class Comment(object):
    def __init__(self, comment):
        self.comment = comment


class Preamble(object):
    def __init__(self, preamble):
        self.preamble = preamble


class String(object):
    def __init__(self, abbreviation, long_form):
        self.abbreviation = abbreviation
        self.long_form = long_form


class Reference(object):
    def __init__(self, comment_above_reference, entry_type, cite_key):
        self.comment_above_reference = comment_above_reference
        self.entry_type = entry_type
        self.cite_key = cite_key

    def get_fields(self):
        return vars(self)

    def __str__(self):
        # print the reference like a dictionary
        fields = self.get_fields()
        field_strings = [f"{key}: {value}" for key, value in fields.items() if key not in ["comment_above_reference", "entry_type"]]
        return "\n".join(field_strings)
        

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
    example_reference = Reference("", "article", "au32")
    example_reference.author = "George"

    # You can add custom attributes to the object dynamically
    # even thought the object has already been instantiated
    example_reference.year = 2004
    example_reference.custom_attribute = "custom value"
    print(example_reference.custom_attribute)

    print(example_reference.get_fields())

    random_file.content.append(example_reference)
    print(random_file.content)
