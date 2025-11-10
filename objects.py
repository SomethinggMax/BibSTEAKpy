from enum import Enum


class BibFile(object):
    def __init__(self, file_name):
        self.file_path = file_name
        self.content = list()

    def __eq__(self, other):
        if not isinstance(other, BibFile):
            return NotImplemented
        return self.file_path == other.file_path and self.content == other.content

    def get_cite_keys(self):
        cite_keys = []
        for entry in self.content:
            if type(entry) is Reference:
                cite_keys.append(entry.cite_key)
        return cite_keys

    def get_reference_by_key(self, cite_key):
        for entry in self.content:
            if type(entry) is Reference:
                if entry.cite_key == cite_key:
                    return entry

    def get_references(self):
        return [entry for entry in self.content if type(entry) is Reference]

    def get_strings(self):
        return [entry for entry in self.content if type(entry) is String]

    def get_comments(self):
        return [entry for entry in self.content if type(entry) is Comment]

    def get_preambles(self):
        return [entry for entry in self.content if isinstance(entry, Preamble)]

    def get_remaining_entries(self):
        """
        Currently there is a single remaining str object if the file ends in something that cannot be parsed.
        :return:
        """
        return [entry for entry in self.content if not isinstance(entry, Reference)
                and not isinstance(entry, String) and not isinstance(entry, Comment)
                and not isinstance(entry, Preamble)]

    def __str__(self):
        return f"[File: {self.file_path} - content: {self.content}]"

    def __repr__(self):
        return self.__str__()


class Comment(object):
    def __init__(self, comment):
        self.comment = comment

    def __eq__(self, other):
        if not isinstance(other, Comment):
            return NotImplemented
        return self.comment == other.comment


class Preamble(object):
    def __init__(self, preamble):
        self.preamble = preamble

    def __eq__(self, other):
        if not isinstance(other, Preamble):
            return NotImplemented
        return self.preamble == other.preamble


class Enclosure(Enum):
    BRACES = 1
    QUOTATION_MARKS = 2


class String(object):
    def __init__(self, comment_above_string, abbreviation, long_form, enclosure=Enclosure.QUOTATION_MARKS):
        self.comment_above_string = comment_above_string
        self.abbreviation = abbreviation
        self.long_form = long_form
        self.enclosure = enclosure

    def __eq__(self, other):
        if not isinstance(other, String):
            return NotImplemented
        return (self.comment_above_string == other.comment_above_string and self.abbreviation == other.abbreviation
                and self.long_form == other.long_form and self.enclosure == other.enclosure)

    def get_fields(self):
        return vars(self)


class Reference(object):
    def __init__(self, comment_above_reference, entry_type, cite_key):
        self.comment_above_reference = comment_above_reference
        self.entry_type = entry_type
        self.cite_key = cite_key

    def __eq__(self, other):
        if not isinstance(other, Reference):
            return NotImplemented
        for (self_field, self_value), (other_field, other_value) in (
                zip(self.get_fields().items(), other.get_fields().items())):
            if self_field != other_field or self_value != other_value:
                return False
        return True

    def get_fields(self):
        return vars(self)

    def __str__(self):
        # print the reference like a dictionary
        fields = self.get_fields()
        field_strings = [f"{key}: {value}" for key, value in fields.items() if
                         key not in ["comment_above_reference", "entry_type"]]
        return "\n".join(field_strings)

    def __repr__(self):
        return self.__str__()


class GraphNode(object):
    def __init__(self, title):
        self.title = title
        self.year = "N/A"


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

    second_reference = Reference("", "article", "au32")
    second_reference.author = "George"
    second_reference.year = 2004
    second_reference.custom_attribute = "custom value"
    assert example_reference == second_reference
    second_reference.author = "Not George"
    assert example_reference != second_reference
    delattr(second_reference, "author")
    setattr(second_reference, "author", "George")
    assert example_reference != second_reference  # Still false since the order is different now.
    delattr(example_reference, "author")
    delattr(second_reference, "author")
    assert example_reference == second_reference  # True since author field is gone
    setattr(example_reference, "Author", "George")
    setattr(second_reference, "author", "George")
    assert example_reference != second_reference  # Fields are different
    delattr(example_reference, "Author")
    setattr(example_reference, "author", "George")
    assert example_reference == second_reference # Now they are the same again
