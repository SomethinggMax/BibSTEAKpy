import re
import unicodedata

from objects import BibFile, Reference


NON_ALNUM_RE = re.compile(r'[^a-z0-9]+')
AUTHOR_SEPARATOR_RE = re.compile(r'\s+and\s+', re.IGNORECASE)


def _strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', value)
    return ''.join(ch for ch in normalized if not unicodedata.combining(ch))


def _prepare_text(value) -> str:
    text = str(value)
    text = text.replace('{', '').replace('}', '')
    text = _strip_diacritics(text)
    return text.lower()


def normalize_author_field(raw_author) -> str:
    if not raw_author:
        return ''

    text = _prepare_text(raw_author)
    people = AUTHOR_SEPARATOR_RE.split(text)
    normalized_people = []

    for person in people:
        tokens = [token for token in NON_ALNUM_RE.split(person) if token]
        if tokens:
            normalized_people.append(''.join(sorted(tokens)))

    if not normalized_people:
        return ''

    normalized_people.sort()
    return '::'.join(normalized_people)


def normalize_title_field(raw_title) -> str:
    if not raw_title:
        return ''

    text = _prepare_text(raw_title)
    return NON_ALNUM_RE.sub('', text)


def build_reference_signature(reference: Reference):
    authors_signature = normalize_author_field(getattr(reference, 'author', None))
    title_signature = normalize_title_field(getattr(reference, 'title', None))

    if authors_signature and title_signature:
        return f'{authors_signature}||{title_signature}'

    return None


def merge_reference(reference_1: Reference, reference_2: Reference) -> Reference:
    merged_reference = Reference(reference_1.comment_above_reference, reference_1.entry_type, reference_1.cite_key)
    reference_1_fields = reference_1.get_fields()
    reference_2_fields = reference_2.get_fields()

    for field_type, data in reference_1_fields.items():
        if field_type in reference_2_fields:
            if data != reference_2_fields[field_type]:                     
                print(f"Conflict in field '{field_type}' for reference key '{reference_1.cite_key}' and '{reference_2.cite_key}':")
                print(f"1. '{data}'")
                print(f"2. '{reference_2_fields[field_type]}'")
                choice = input('Choose which to keep (1 or 2): ')
                if choice == '2':
                    data = reference_2_fields[field_type]
        setattr(merged_reference, field_type, data)  # add field from reference 1 to merged reference

    for field_type, data in reference_2_fields.items():
        if field_type not in merged_reference.get_fields():
            setattr(merged_reference, field_type, data)  # add field from reference 2 to merged reference

    return merged_reference


def merge_files(bib_file_1: BibFile, bib_file_2: BibFile) -> BibFile:
    # File name will be set when generating the file, this is just temporary.
    merged_bib_file = BibFile(bib_file_1.file_name + '+' + bib_file_2.file_name)

    # Add all strings first.
    merged_bib_file.content = bib_file_1.get_strings()
    merged_bib_file.content.extend(bib_file_2.get_strings())

    bib2_reference_by_key = {
        entry.cite_key: entry
        for entry in bib_file_2.content
        if isinstance(entry, Reference)
    }

    bib2_signatures = {}
    for reference in bib2_reference_by_key.values():
        signature = build_reference_signature(reference)
        if signature:
            bib2_signatures.setdefault(signature, []).append(reference.cite_key)

    consumed_bib2_keys = set()

    # Add references from bib file 1.
    for entry in bib_file_1.content:
        if isinstance(entry, Reference):
            if entry.cite_key in bib2_reference_by_key:
                merged_reference = merge_reference(entry, bib2_reference_by_key[entry.cite_key])
                merged_bib_file.content.append(merged_reference)
                consumed_bib2_keys.add(entry.cite_key)
                continue

            signature = build_reference_signature(entry)
            if signature:
                candidate_keys = [
                    key for key in bib2_signatures.get(signature, [])
                    if key not in consumed_bib2_keys
                ]
                if candidate_keys:
                    target_key = candidate_keys[0]
                    print("References seem to be similar based on author/title normalization.")
                    print("Please compare the following references:")
                    print(f"Reference 1 (from first file):\n{entry}\n")
                    print(f"Reference 2 (from second file):\n{bib2_reference_by_key[target_key]}\n")
                    print("Choose where to merge or skip:")
                    print("1: Merge references")
                    print("2: Keep both references")
                    choice = input("Enter your choice (1 or 2): ")
                    if choice == '1':
                        print(
                            f"Merging '{entry.cite_key}' with '{target_key}' based on normalized author/title match."
                        )
                        merged_reference = merge_reference(entry, bib2_reference_by_key[target_key])
                        merged_bib_file.content.append(merged_reference)
                        consumed_bib2_keys.add(target_key)
                        continue
                    elif choice == '2':
                        print(f"Skipping merge for '{entry.cite_key}'. Keeping both entries.")
                        merged_bib_file.content.append(entry)
                        merged_bib_file.content.append(bib2_reference_by_key[target_key])
                        consumed_bib2_keys.add(target_key)
                        continue
                    else:
                        raise ValueError("Invalid choice. Please enter 1 or 2.")

            merged_bib_file.content.append(entry)

    # Add remaining references from bib file 2.
    for entry in bib_file_2.content:
        if isinstance(entry, Reference) and entry.cite_key not in consumed_bib2_keys:
            merged_bib_file.content.append(entry)

    return merged_bib_file
