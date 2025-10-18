import os
import re
import sys
import textwrap
import unicodedata
from urllib.parse import urlparse

from objects import BibFile, Reference, String
from utils import batch_editor
from difflib import SequenceMatcher


NON_ALNUM_RE = re.compile(r'[^a-z0-9]+')
AUTHOR_SEPARATOR_RE = re.compile(r'\s+and\s+', re.IGNORECASE)

# Similarity thresholds for abstract comparison
ABSTRACT_STRONG_MATCH = 0.9
ABSTRACT_STRONG_MISMATCH = 0.5

# Pretty printing / CLI formatting
PREFERRED_FIELD_ORDER = [
    'cite_key', 'author', 'title', 'year', 'journal', 'booktitle', 'publisher',
    'volume', 'number', 'pages', 'doi', 'url', 'isbn', 'issn', 'abstract'
]

# URL domains considered relatively reliable for identity matching
TRUSTED_URL_DOMAINS = {
    'doi.org', 'dx.doi.org', 'arxiv.org', 'dl.acm.org', 'ieeexplore.ieee.org',
    'link.springer.com', 'www.nature.com', 'nature.com', 'science.org',
    'pubmed.ncbi.nlm.nih.gov', 'openreview.net'
}


def _supports_color() -> bool:
    try:
        return sys.stdout.isatty() and not os.environ.get('NO_COLOR')
    except Exception:
        return False


ANSI = {
    'reset': '\x1b[0m',
    'dim': '\x1b[2m',
    'bold': '\x1b[1m',
    'red': '\x1b[31m',
    'green': '\x1b[32m',
    'yellow': '\x1b[33m',
}


def _colorize(text: str, color: str) -> str:
    if not _supports_color() or color not in ANSI:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def _stringify_field_value(value) -> str:
    s = str(value) if value is not None else ''
    # Remove extraneous braces to reduce noise and normalize whitespace
    s = s.replace('{', '').replace('}', '')
    s = _normalize_whitespace(s)
    return s


def _ordered_field_names(ref: Reference) -> list:
    fields = list(ref.get_fields().keys())
    # Remove internal/meta fields from display ordering context
    for k in ["comment_above_reference", "entry_type"]:
        if k in fields:
            fields.remove(k)
    # Always include cite_key if present
    def order_key(name: str):
        return (PREFERRED_FIELD_ORDER.index(name) if name in PREFERRED_FIELD_ORDER else len(PREFERRED_FIELD_ORDER), name)

    return sorted(fields, key=order_key)


def _collect_all_fields(ref1: Reference, ref2: Reference) -> list:
    names = set(_ordered_field_names(ref1)) | set(_ordered_field_names(ref2))
    def order_key(name: str):
        return (PREFERRED_FIELD_ORDER.index(name) if name in PREFERRED_FIELD_ORDER else len(PREFERRED_FIELD_ORDER), name)
    return sorted(names, key=order_key)


def print_reference_comparison(ref1: Reference, ref2: Reference, width: int = 100, left_col: int = 18) -> None:
    # Calculate widths for a simple side-by-side view
    value_width = max(20, (width - left_col - 7) // 2)  # account for separators
    header = f"{'Field'.ljust(left_col)} | {'Ref 1'.ljust(value_width)} | {'Ref 2'.ljust(value_width)}"
    sep = '-' * len(header)
    print(_colorize(header, 'bold'))
    print(_colorize(sep, 'dim'))

    for name in _collect_all_fields(ref1, ref2):
        v1 = _stringify_field_value(getattr(ref1, name, ''))
        v2 = _stringify_field_value(getattr(ref2, name, ''))

        # For very long fields like abstract, wrap to value_width and cap to a few lines for readability
        def wrap(s: str) -> list:
            if not s:
                return ['']
            wrapped = textwrap.wrap(s, width=value_width, replace_whitespace=False, drop_whitespace=False)
            # Show max 4 lines to keep prompt readable
            return wrapped[:4] + (["…"] if len(wrapped) > 4 else [])

        lines1 = wrap(v1)
        lines2 = wrap(v2)
        max_lines = max(len(lines1), len(lines2))
        is_diff = (v1 != v2)

        name_cell = name.ljust(left_col)
        for i in range(max_lines):
            l = lines1[i] if i < len(lines1) else ''
            r = lines2[i] if i < len(lines2) else ''
            row = f"{name_cell if i == 0 else ' ' * left_col} | {l.ljust(value_width)} | {r.ljust(value_width)}"
            print(_colorize(row, 'red') if is_diff else row)

    print(_colorize(sep, 'dim'))


def _strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', value)
    return ''.join(ch for ch in normalized if not unicodedata.combining(ch))


def _prepare_text(value) -> str:
    text = str(value)
    text = text.replace('{', '').replace('}', '')
    text = _strip_diacritics(text)
    return text.lower()


def _normalize_whitespace(value: str) -> str:
    return ' '.join(value.split())


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


def normalize_abstract_field(raw_abstract) -> str:
    if not raw_abstract:
        return ''

    text = _prepare_text(raw_abstract)
    # Keep spaces for better sequence similarity, but collapse runs
    text = re.sub(r'[^a-z0-9\s]+', ' ', text)
    return _normalize_whitespace(text)


def abstract_similarity(a, b) -> float:
    a_norm = normalize_abstract_field(getattr(a, 'abstract', None) if isinstance(a, Reference) else a)
    b_norm = normalize_abstract_field(getattr(b, 'abstract', None) if isinstance(b, Reference) else b)
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


def _normalize_year(value) -> str:
    if value is None:
        return ''
    s = str(value)
    m = re.search(r'(\d{4})', s)
    return m.group(1) if m else ''


def _normalize_pages(value) -> str:
    if value is None:
        return ''
    s = str(value)
    s = s.replace('\u2013', '-').replace('\u2014', '-')  # en/em dash to hyphen
    s = re.sub(r'\s*[-–—]+\s*', '-', s)
    # Use BibTeX-style double dash between numeric ranges
    s = re.sub(r'(?<=\d)-(?!-)(?=\d)', '--', s)
    return s


def _normalize_doi(value) -> str:
    if not value:
        return ''
    s = str(value).strip().lower()
    # Remove common prefixes
    s = re.sub(r'^\s*doi\s*:?', '', s).strip()
    s = re.sub(r'^https?://(dx\.)?doi\.org/', '', s)
    # Strip enclosing quotes/braces and spaces
    s = s.strip().strip('{}"\'')
    # Remove whitespace and angle brackets sometimes used around DOIs
    s = re.sub(r'[\s<>]+', '', s)
    # Drop trailing punctuation
    s = re.sub(r'[\.,;:]+$', '', s)
    return s


def _normalize_url(value) -> str:
    if not value:
        return ''
    s = str(value).strip()
    # Normalize trivial differences
    s = re.sub(r'\s+', '', s)
    return s


def _canonical_url_key(value) -> str | None:
    if not value:
        return None
    s = str(value).strip()
    try:
        p = urlparse(s)
        domain = (p.netloc or '').lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        path = (p.path or '').rstrip('/')
        # If doi.org URL, reduce to DOI string for consistency
        if domain in ('doi.org', 'dx.doi.org'):
            doi = re.sub(r'^/+', '', path)
            doi = _normalize_doi(doi)
            return f'doi:{doi}' if doi else None
        if not domain:
            return None
        return f'{domain}|{path}'
    except Exception:
        return None


def _split_enclosure(value):
    s = str(value) if value is not None else ''
    s = s.strip()
    if len(s) >= 2 and s[0] == '{' and s[-1] == '}':
        return ('braces', s[1:-1])
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return ('quotes', s[1:-1])
    return (None, s)


def _apply_enclosure(enclosure, inner: str) -> str:
    if enclosure == 'braces':
        return '{' + inner + '}'
    if enclosure == 'quotes':
        return '"' + inner + '"'
    return inner


def _choose_enclosure(v1, v2):
    e1, _ = _split_enclosure(v1)
    e2, _ = _split_enclosure(v2)
    return e1 or e2 or 'braces'


def normalize_field_for_compare(field: str, value) -> str:
    f = (field or '').lower()
    if f == 'author':
        return normalize_author_field(value)
    if f == 'title':
        return normalize_title_field(value)
    if f == 'abstract':
        return normalize_abstract_field(value)
    if f == 'year':
        return _normalize_year(value)
    if f == 'pages':
        return _normalize_pages(value)
    if f == 'doi':
        return _normalize_doi(value)
    if f == 'url':
        return _normalize_url(value)
    # Default: lowercased, trimmed, braces removed, whitespace normalized
    return _normalize_whitespace(str(value).replace('{', '').replace('}', '').lower()) if value is not None else ''


def _brace_stats(value: str) -> tuple:
    if value is None:
        return (False, 0)
    s = str(value)
    return (s.count('{') == s.count('}'), s.count('{') + s.count('}'))


def canonicalize_field_value(field: str, v1, v2):
    f = (field or '').lower()
    if f == 'year':
        y = _normalize_year(v1) or _normalize_year(v2)
        enc = _choose_enclosure(v1, v2)
        return _apply_enclosure(enc, y) if y else ''
    if f == 'pages':
        # Prefer a canonical pages representation derived from either
        base = v1 if _normalize_pages(v1) else v2
        p = _normalize_pages(base)
        enc = _choose_enclosure(v1, v2)
        return _apply_enclosure(enc, p) if p else ''
    if f == 'doi':
        d = _normalize_doi(v1) or _normalize_doi(v2)
        enc = _choose_enclosure(v1, v2)
        return _apply_enclosure(enc, d) if d else ''
    if f == 'url':
        # Prefer https if both share same host/path differing only by scheme
        u1 = str(v1).strip() if v1 else ''
        u2 = str(v2).strip() if v2 else ''
        if u1.lower().replace('http://', 'https://') == u2.lower().replace('http://', 'https://'):
            chosen = u1 if u1.lower().startswith('https://') else (u2 if u2.lower().startswith('https://') else u1 or u2)
        else:
            chosen = _normalize_url(v1) or _normalize_url(v2)
        enc = _choose_enclosure(v1, v2)
        inner = re.sub(r'^"|"$|^\{|\}$', '', chosen)
        return _apply_enclosure(enc, inner) if inner else ''
    if f in ('title', 'author', 'journal', 'booktitle', 'publisher'):
        # Prefer the version with balanced and fewer braces; otherwise v1
        b1 = _brace_stats(v1)
        b2 = _brace_stats(v2)
        if b1[0] and not b2[0]:
            return v1
        if b2[0] and not b1[0]:
            return v2
        if b1[0] and b2[0]:
            if b1[1] != b2[1]:
                return v1 if b1[1] < b2[1] else v2
        # Fall back to the one with cleaner whitespace
        s1 = _normalize_whitespace(str(v1 or ''))
        s2 = _normalize_whitespace(str(v2 or ''))
        return v1 if len(s1) <= len(s2) else v2
    # Default: choose shorter trimmed representation
    s1 = _normalize_whitespace(str(v1 or ''))
    s2 = _normalize_whitespace(str(v2 or ''))
    return v1 if len(s1) <= len(s2) else v2


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
            other = reference_2_fields[field_type]
            # Skip meta fields
            if field_type in ("comment_above_reference", "entry_type"):
                setattr(merged_reference, field_type, data)
                continue

            # If equal after normalization, prefer a canonical/cleaner representation without prompting
            if normalize_field_for_compare(field_type, data) == normalize_field_for_compare(field_type, other):
                chosen = canonicalize_field_value(field_type, data, other)
                setattr(merged_reference, field_type, chosen)
                continue

            if data != other:
                print(_colorize(f"Conflict in field '{field_type}' for key '{reference_1.cite_key}':", 'yellow'))
                # Pretty print just the conflicting field values side-by-side
                temp1 = Reference(reference_1.comment_above_reference, reference_1.entry_type, reference_1.cite_key)
                temp2 = Reference(reference_2.comment_above_reference, reference_2.entry_type, reference_2.cite_key)
                setattr(temp1, field_type, data)
                setattr(temp2, field_type, other)
                print_reference_comparison(temp1, temp2, width=100)
                choice = input('Choose which to keep (1 or 2): ')
                if choice == '1':
                    data = data
                elif choice == '2':
                    data = other
                else:
                    raise ValueError("Invalid choice. Please enter 1 or 2.")    
        setattr(merged_reference, field_type, data)  # add field from reference 1 to merged reference

    for field_type, data in reference_2_fields.items():
        if field_type not in merged_reference.get_fields():
            setattr(merged_reference, field_type, data)  # add field from reference 2 to merged reference

    return merged_reference


def merge_strings(bib_file_1: BibFile, bib_file_2: BibFile) -> (BibFile, BibFile, [String]):
    """
    Merge the Strings from two bib files together into a single list of Strings.
    :param bib_file_1: the first file.
    :param bib_file_2: the second file.
    :return: (bib_file_1, bib_file_2, string_list), updated bib files with a list of the strings for the merged file.
    """
    string_list = []
    file_2_strings = {x.abbreviation: x.long_form for x in bib_file_2.get_strings()}
    for string in bib_file_1.get_strings():
        if string.abbreviation not in file_2_strings:
            string_list.append(string)
        elif file_2_strings[string.abbreviation] == string.long_form:
            string_list.append(string)
        else:
            print(f"Conflict with string abbreviation '{string.abbreviation}'!")
            print("You can select an abbreviation to rename.")
            print(f"1: {string.long_form}")
            print(f"2: {file_2_strings[string.abbreviation]}")
            choice = input("Enter your choice (1 or 2): ")
            new_abbreviation = input(f"Now input the new abbreviation for '{string.long_form}'. "
                                     f"(Old abbreviation: '{string.abbreviation}'): ")
            if choice == '1':
                old_abbreviation = string.abbreviation
                batch_editor.batch_rename_abbreviation(bib_file_1, string.abbreviation, new_abbreviation)
                string_list.append([x for x in bib_file_1.get_strings() if x.abbreviation == new_abbreviation][0])
                string_list.append([x for x in bib_file_2.get_strings() if x.abbreviation == old_abbreviation][0])
            elif choice == '2':
                batch_editor.batch_rename_abbreviation(bib_file_2, string.abbreviation, new_abbreviation)
                string_list.append(string)  # The unchanged string from file 1.
                string_list.append([x for x in bib_file_2.get_strings() if x.abbreviation == new_abbreviation][0])
            else:
                raise ValueError("Invalid choice. Please enter 1 or 2.")
    return bib_file_1, bib_file_2, string_list


def merge_files(bib_file_1: BibFile, bib_file_2: BibFile) -> BibFile:
    # File name will be set when generating the file, this is just temporary.
    merged_bib_file = BibFile(bib_file_1.file_name + '+' + bib_file_2.file_name)

    merged_bib_file.content = bib_file_1.get_preambles()  # Add preambles from file 1.

    # Add preambles from file 2 if they are different.
    preamble_contents = [x.preamble for x in bib_file_1.get_preambles()]
    for preamble in bib_file_2.get_preambles():
        if preamble.preamble not in preamble_contents:
            merged_bib_file.content.append(preamble)

    bib_file_1, bib_file_2, string_list = merge_strings(bib_file_1, bib_file_2)
    merged_bib_file.content.extend(string_list)

    # Build signature index for file 2 based on normalized author+title only
    bib2_index = {
        entry.cite_key: entry
        for entry in bib_file_2.content
        if isinstance(entry, Reference)
    }

    # Build DOI and URL indexes for file 2
    bib2_doi_index = {}
    bib2_url_index = {}

    bib2_signatures = {}
    for reference in bib2_index.values():
        signature = build_reference_signature(reference)
        if signature:
            bib2_signatures.setdefault(signature, []).append(reference.cite_key)
        # DOI index
        doi_norm = _normalize_doi(getattr(reference, 'doi', None))
        if doi_norm:
            bib2_doi_index.setdefault(doi_norm, []).append(reference.cite_key)
        # URL index (trusted domains only)
        url_key = _canonical_url_key(getattr(reference, 'url', None))
        if url_key:
            domain = url_key.split('|', 1)[0]
            if domain in TRUSTED_URL_DOMAINS or url_key.startswith('doi:'):
                bib2_url_index.setdefault(url_key, []).append(reference.cite_key)

    consumed_bib2_keys = set()

    # Add references from bib file 1.
    for entry in bib_file_1.content:
        if isinstance(entry, Reference):
            # 1) Try DOI match for auto-merge
            doi_norm = _normalize_doi(getattr(entry, 'doi', None))
            if doi_norm:
                candidate_keys = [
                    key for key in bib2_doi_index.get(doi_norm, [])
                    if key not in consumed_bib2_keys
                ]
                if candidate_keys:
                    # Choose best by abstract similarity if multiple
                    best_key = candidate_keys[0]
                    if len(candidate_keys) > 1:
                        best_sim = -1.0
                        for key in candidate_keys:
                            sim = abstract_similarity(entry, bib2_index[key])
                            if sim > best_sim:
                                best_sim = sim
                                best_key = key
                    target_key = best_key
                    other_ref = bib2_index[target_key]
                    print(
                        f"Auto-merging '{entry.cite_key}' + '{target_key}' (matched DOI)."
                    )
                    merged_reference = merge_reference(entry, other_ref)
                    merged_bib_file.content.append(merged_reference)
                    consumed_bib2_keys.add(target_key)
                    continue

            # 2) Try author+title signature matching
            signature = build_reference_signature(entry)
            if signature:
                candidate_keys = [
                    key for key in bib2_signatures.get(signature, [])
                    if key not in consumed_bib2_keys
                ]
                if candidate_keys:
                    # If multiple candidates share the same signature, pick the one with highest abstract similarity
                    best_key = None
                    best_sim = -1.0
                    for key in candidate_keys:
                        sim = abstract_similarity(entry, bib2_index[key])
                        if sim > best_sim:
                            best_sim = sim
                            best_key = key

                    target_key = best_key
                    other_ref = bib2_index[target_key]

                    # Decide based on abstract similarity if abstracts exist
                    has_abs_1 = bool(normalize_abstract_field(getattr(entry, 'abstract', None)))
                    has_abs_2 = bool(normalize_abstract_field(getattr(other_ref, 'abstract', None)))

                    if has_abs_1 and has_abs_2:
                        if best_sim >= ABSTRACT_STRONG_MATCH:
                            print(
                                f"Auto-merging '{entry.cite_key}' + '{target_key}' (author/title match, abstract sim {best_sim:.2f})."
                            )
                            merged_reference = merge_reference(entry, other_ref)
                            merged_bib_file.content.append(merged_reference)
                            consumed_bib2_keys.add(target_key)
                            continue
                        elif best_sim <= ABSTRACT_STRONG_MISMATCH:
                            print(
                                f"Keeping both for '{entry.cite_key}' and '{target_key}' (low abstract sim {best_sim:.2f})."
                            )
                            merged_bib_file.content.append(entry)
                            merged_bib_file.content.append(other_ref)
                            consumed_bib2_keys.add(target_key)
                            continue

                    # Otherwise, ask user
                    print("References seem similar based on author/title normalization.")
                    if has_abs_1 and has_abs_2:
                        print(f"Abstract similarity: {best_sim:.2f}")
                    print("Please compare the following references:")
                    print_reference_comparison(entry, other_ref, width=110)
                    print("Choose where to merge or skip:")
                    print("1: Merge references")
                    print("2: Keep both references")
                    choice = input("Enter your choice (1 or 2): ")
                    if choice == '1':
                        print(
                            f"Merging '{entry.cite_key}' with '{target_key}' based on normalized author/title match."
                        )
                        merged_reference = merge_reference(entry, other_ref)
                        merged_bib_file.content.append(merged_reference)
                        consumed_bib2_keys.add(target_key)
                        continue
                    elif choice == '2':
                        print(f"Skipping merge for '{entry.cite_key}'. Keeping both entries.")
                        merged_bib_file.content.append(entry)
                        merged_bib_file.content.append(other_ref)
                        consumed_bib2_keys.add(target_key)
                        continue
                    else:
                        raise ValueError("Invalid choice. Please enter 1 or 2.")

            # 3) Try URL match on trusted domains (prompt)
            url_key = _canonical_url_key(getattr(entry, 'url', None))
            if url_key:
                domain = url_key.split('|', 1)[0]
                if domain in TRUSTED_URL_DOMAINS or url_key.startswith('doi:'):
                    candidate_keys = [
                        key for key in bib2_url_index.get(url_key, [])
                        if key not in consumed_bib2_keys
                    ]
                    if candidate_keys:
                        # If multiple, show the best by abstract similarity
                        best_key = candidate_keys[0]
                        if len(candidate_keys) > 1:
                            best_sim = -1.0
                            for key in candidate_keys:
                                sim = abstract_similarity(entry, bib2_index[key])
                                if sim > best_sim:
                                    best_sim = sim
                                    best_key = key
                        target_key = best_key
                        other_ref = bib2_index[target_key]
                        print("References share the same trusted URL; please confirm merge.")
                        print_reference_comparison(entry, other_ref, width=110)
                        print("Choose where to merge or skip:")
                        print("1: Merge references")
                        print("2: Keep both references")
                        choice = input("Enter your choice (1 or 2): ")
                        if choice == '1':
                            print(
                                f"Merging '{entry.cite_key}' with '{target_key}' based on URL match."
                            )
                            merged_reference = merge_reference(entry, other_ref)
                            merged_bib_file.content.append(merged_reference)
                            consumed_bib2_keys.add(target_key)
                            continue
                        elif choice == '2':
                            print(f"Skipping merge for '{entry.cite_key}'. Keeping both entries.")
                            merged_bib_file.content.append(entry)
                            merged_bib_file.content.append(other_ref)
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
