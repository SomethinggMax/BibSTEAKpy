from copy import copy
from objects import BibFile, Reference, String, Comment
from utils import json_loader


def convert_symbols(reference: Reference):
    bibtex_to_unicode = {
        # Umlauts
        '{\\"a}': 'ä', '{\\"{a}}': 'ä', '\\"{a}': 'ä', '{\\" a}': 'ä',
        '{\\"e}': 'ë', '{\\"{e}}': 'ë', '\\"{e}': 'ë', '{\\" e}': 'ë',
        '{\\"i}': 'ï', '{\\"{i}}': 'ï', '\\"{i}': 'ï', '{\\" i}': 'ï', '{\\"{\\i}}': 'ï',
        '{\\"o}': 'ö', '{\\"{o}}': 'ö', '\\"{o}': 'ö', '{\\" o}': 'ö',
        '{\\"u}': 'ü', '{\\"{u}}': 'ü', '\\"{u}': 'ü', '{\\" u}': 'ü',
        '{\\"A}': 'Ä', '{\\"{A}}': 'Ä', '\\"{A}': 'Ä', '{\\" A}': 'Ä',
        '{\\"E}': 'Ë', '{\\"{E}}': 'Ë', '\\"{E}': 'Ë', '{\\" E}': 'Ë',
        '{\\"I}': 'Ï', '{\\"{I}}': 'Ï', '\\"{I}': 'Ï', '{\\" I}': 'Ï', '{\\"{\\I}}': 'Ï',
        '{\\"O}': 'Ö', '{\\"{O}}': 'Ö', '\\"{O}': 'Ö', '{\\" O}': 'Ö',
        '{\\"U}': 'Ü', '{\\"{U}}': 'Ü', '\\"{U}': 'Ü', '{\\" U}': 'Ü',

        # Acute accents
        "{\\'a}": 'á', "\\'{a}": 'á', "{\\' a}": 'á',
        "{\\'e}": 'é', "\\'{e}": 'é', "{\\' e}": 'é',
        "{\\'i}": 'í', "\\'{i}": 'í', "{\\' i}": 'í', "{\\'\\i}": 'í', "{\\'{\\i}}": 'í', "\\'{\\i}": 'í',
        "{\\'o}": 'ó', "\\'{o}": 'ó', "{\\' o}": 'ó',
        "{\\'u}": 'ú', "\\'{u}": 'ú', "{\\' u}": 'ú',
        "{\\'y}": 'ý', "\\'{y}": 'ý', "{\\' y}": 'ý',
        "{\\'c}": 'ć', "\\'{c}": 'ć', "{\\' c}": 'ć',
        "{\\'A}": 'Á', "\\'{A}": 'Á', "{\\' A}": 'Á',
        "{\\'E}": 'É', "\\'{E}": 'É', "{\\' E}": 'É',
        "{\\'I}": 'Í', "\\'{I}": 'Í', "{\\' I}": 'Í', "{\\'{I}}": 'Í',
        "{\\'O}": 'Ó', "\\'{O}": 'Ó', "{\\' O}": 'Ó',
        "{\\'U}": 'Ú', "\\'{U}": 'Ú', "{\\' U}": 'Ú',
        "{\\'Y}": 'Ý', "\\'{Y}": 'Ý', "{\\' Y}": 'Ý',
        "{\\'C}": 'Ć', "\\'{C}": 'Ć', "{\\' C}": 'Ć',

        # Grave accents
        '{\\`a}': 'à', '\\`{a}': 'à', '{\\` a}': 'à',
        '{\\`e}': 'è', '\\`{e}': 'è', '{\\` e}': 'è',
        '{\\`i}': 'ì', '\\`{i}': 'ì', '{\\` i}': 'ì',
        '{\\`o}': 'ò', '\\`{o}': 'ò', '{\\` o}': 'ò',
        '{\\`u}': 'ù', '\\`{u}': 'ù', '{\\` u}': 'ù',
        '{\\`A}': 'À', '\\`{A}': 'À', '{\\` A}': 'À',
        '{\\`E}': 'È', '\\`{E}': 'È', '{\\` E}': 'È',
        '{\\`I}': 'Ì', '\\`{I}': 'Ì', '{\\` I}': 'Ì',
        '{\\`O}': 'Ò', '\\`{O}': 'Ò', '{\\` O}': 'Ò',
        '{\\`U}': 'Ù', '\\`{U}': 'Ù', '{\\` U}': 'Ù',

        # Circumflex
        '{\\^a}': 'â', '\\^{a}': 'â', '{\\^ a}': 'â',
        '{\\^e}': 'ê', '\\^{e}': 'ê', '{\\^ e}': 'ê',
        '{\\^i}': 'î', '\\^{i}': 'î', '{\\^ i}': 'î', '{\\^\\i}': 'î', '{\\^{\\i}}': 'î',
        '{\\^o}': 'ô', '\\^{o}': 'ô', '{\\^ o}': 'ô',
        '{\\^u}': 'û', '\\^{u}': 'û', '{\\^ u}': 'û',
        '{\\^A}': 'Â', '\\^{A}': 'Â', '{\\^ A}': 'Â',
        '{\\^E}': 'Ê', '\\^{E}': 'Ê', '{\\^ E}': 'Ê',
        '{\\^I}': 'Î', '\\^{I}': 'Î', '{\\^ I}': 'Î',
        '{\\^O}': 'Ô', '\\^{O}': 'Ô', '{\\^ O}': 'Ô',
        '{\\^U}': 'Û', '\\^{U}': 'Û', '{\\^ U}': 'Û',

        # Tilde
        '{\\~a}': 'ã', '\\~{a}': 'ã', '{\\~ a}': 'ã',
        '{\\~n}': 'ñ', '\\~{n}': 'ñ', '{\\~ n}': 'ñ',
        '{\\~o}': 'õ', '\\~{o}': 'õ', '{\\~ o}': 'õ',
        '{\\~A}': 'Ã', '\\~{A}': 'Ã', '{\\~ A}': 'Ã',
        '{\\~N}': 'Ñ', '\\~{N}': 'Ñ', '{\\~ N}': 'Ñ',
        '{\\~O}': 'Õ', '\\~{O}': 'Õ', '{\\~ O}': 'Õ',

        # Ring
        '{\\aa}': 'å', '\\aa': 'å',
        '{\\AA}': 'Å', '\\AA': 'Å',

        # Cedilla
        '{\\c{c}}': 'ç', '\\c{c}': 'ç', '{\\c c}': 'ç',
        '{\\c{s}}': 'ş', '\\c{s}': 'ş', '{\\c s}': 'ş',
        '{\\c{C}}': 'Ç', '\\c{C}': 'Ç', '{\\c C}': 'Ç',
        '{\\c{S}}': 'Ş', '\\c{S}': 'Ş', '{\\c S}': 'Ş',

        # Caron (háček)
        '{\\v{c}}': 'č', '\\v{c}': 'č', '{\\v c}': 'č',
        '{\\v{s}}': 'š', '\\v{s}': 'š', '{\\v s}': 'š',
        '{\\v{z}}': 'ž', '\\v{z}': 'ž', '{\\v z}': 'ž',
        '{\\v{C}}': 'Č', '\\v{C}': 'Č', '{\\v C}': 'Č',
        '{\\v{S}}': 'Š', '\\v{S}': 'Š', '{\\v S}': 'Š',
        '{\\v{Z}}': 'Ž', '\\v{Z}': 'Ž', '{\\v Z}': 'Ž',

        # Hungarian double acute accent
        '{\\H{o}}': 'ő', '\\H{o}': 'ő',
        '{\\H{O}}': 'Ő', '\\H{O}': 'Ő',
        '{\\H{u}}': 'ű', '\\H{u}': 'ű',
        '{\\H{U}}': 'Ű', '\\H{U}': 'Ű',

        # Breve
        '{\\u{a}}': 'ă', '\\u{a}': 'ă',
        '{\\u{e}}': 'ă', '\\u{e}': 'ă',
        '{\\u{i}}': 'ĭ', '\\u{i}': 'ĭ',
        '{\\u{o}}': 'ŏ', '\\u{o}': 'ŏ',
        '{\\u{u}}': 'ŭ', '\\u{u}': 'ŭ',
        '{\\u{A}}': 'Ă', '\\u{A}': 'Ă',
        '{\\u{E}}': 'Ĕ', '\\u{E}': 'Ĕ',
        '{\\u{I}}': 'Ĭ', '\\u{I}': 'Ĭ',
        '{\\u{O}}': 'Ŏ', '\\u{O}': 'Ŏ',
        '{\\u{U}}': 'Ŭ', '\\u{U}': 'Ŭ',

        # Ogonek
        '{\\k{a}}': 'ą', '\\k{a}': 'ą',
        '{\\k{e}}': 'ę', '\\k{e}': 'ę',
        '{\\k{i}}': 'į', '\\k{i}': 'į',
        '{\\k{o}}': 'ǫ', '\\k{o}': 'ǫ',
        '{\\k{u}}': 'ų', '\\k{u}': 'ų',
        '{\\k{A}}': 'Ą', '\\k{A}': 'Ą',
        '{\\k{E}}': 'Ę', '\\k{E}': 'Ę',
        '{\\k{I}}': 'Į', '\\k{I}': 'Į',
        '{\\k{O}}': 'Ǫ', '\\k{O}': 'Ǫ',
        '{\\k{U}}': 'Ų', '\\k{U}': 'Ų',

        # Macron
        '{\\=a}': 'ā', '{\\={a}}': 'ā', '\\={a}': 'ā', '{\\= a}': 'ā',
        '{\\=e}': 'ē', '{\\={e}}': 'ē', '\\={e}': 'ē', '{\\= e}': 'ē',
        '{\\=i}': 'ī', '{\\={i}}': 'ī', '\\={i}': 'ī', '{\\= i}': 'ī',
        '{\\=o}': 'ō', '{\\={o}}': 'ō', '\\={o}': 'ō', '{\\= o}': 'ō',
        '{\\=u}': 'ū', '{\\={u}}': 'ū', '\\={u}': 'ū', '{\\= u}': 'ū',
        '{\\=p}': 'p̄', '{\\={p}}': 'p̄', '\\={p}': 'p̄', '{\\= p}': 'p̄',
        '{\\=A}': 'Ā', '{\\={A}}': 'Ā', '\\={A}': 'Ā', '{\\= A}': 'Ā',
        '{\\=E}': 'Ē', '{\\={E}}': 'Ē', '\\={E}': 'Ē', '{\\= E}': 'Ē',
        '{\\=I}': 'Ī', '{\\={I}}': 'Ī', '\\={I}': 'Ī', '{\\= I}': 'Ī',
        '{\\=O}': 'Ō', '{\\={O}}': 'Ō', '\\={O}': 'Ō', '{\\= O}': 'Ō',
        '{\\=U}': 'Ū', '{\\={U}}': 'Ū', '\\={U}': 'Ū', '{\\= U}': 'Ū',
        '{\\=P}': 'P̄', '{\\={P}}': 'P̄', '\\={P}': 'P̄', '{\\= P}': 'P̄',

        # Other special letters
        '{\\ss}': 'ß', '\\ss': 'ß',
        '{\\o}': 'ø', '\\o': 'ø',
        '{\\O}': 'Ø', '\\O': 'Ø',
        '{\\ae}': 'æ', '\\ae': 'æ',
        '{\\AE}': 'Æ', '\\AE': 'Æ',
        '{\\l}': 'ł', '\\l': 'ł',
        '{\\L}': 'Ł', '\\L': 'Ł'
    }
    for field_type, data in reference.get_fields().items():
        if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
            continue
        for key, value in bibtex_to_unicode.items():
            data = data.replace(key, value)
        if "\\" in data and "http" not in data and "www" not in data and "10.10" not in data:
            print(f"Data containing '\\': {data}")


def clean_url_and_doi(reference: Reference, use_url, use_doi) -> Reference:
    fields = reference.get_fields()
    url_field = fields.get("url")
    doi_field = fields.get("doi")

    # Delete both if url and doi are false.
    if not use_url and not use_doi:
        if url_field:
            delattr(reference, "url")
        if doi_field:
            delattr(reference, "doi")
    # Else only delete when both fields exist.
    elif url_field and doi_field:
        if not use_url:
            delattr(reference, "url")
        if not use_doi:
            delattr(reference, "doi")
    return reference


def remove_fields(reference: Reference, fields: [str]) -> Reference:
    for field in fields:
        if field in reference.get_fields():
            delattr(reference, field)
    return reference


def remove_comments(bib_file: BibFile):
    for entry in bib_file.content:
        if isinstance(entry, Reference):
            entry.comment_above_reference = ""
        elif isinstance(entry, String):
            entry.comment_above_string = ""
        elif isinstance(entry, str):
            bib_file.content.remove(entry)


def remove_comment_entries(bib_file: BibFile):
    for entry in bib_file.content:
        if isinstance(entry, Comment):
            bib_file.content.remove(entry)


def lower_entry_type(reference: Reference):
    reference.entry_type = reference.entry_type.lower()


def lower_fields(reference: Reference):
    for field_type, data in copy(reference).get_fields().items():
        delattr(reference, field_type)
        setattr(reference, field_type.lower(), data)


def change_field_enclosure(reference: Reference, start_enclosure: str, end_enclosure: str):
    for field_type, data in reference.get_fields().items():
        if field_type == "comment_above_reference" or field_type == "entry_type" or field_type == "cite_key":
            continue
        if ' # ' in data:
            continue
        new_data = remove_enclosure(data)
        if new_data == data:
            continue
        if not new_data.isdigit():
            new_data = start_enclosure + new_data + end_enclosure
        setattr(reference, field_type, new_data)


def remove_enclosure(field_value: str) -> str:
    start_enclosure = ""
    end_enclosure = ""
    for char in field_value:
        if char == '{':
            start_enclosure += char
        elif char == '"':
            start_enclosure += char
        else:
            break
    for char in reversed(field_value):
        if char == '}':
            end_enclosure += '{'
        elif char == '"':
            end_enclosure += char
        else:
            break

    # Remove enclosure while start and end enclosure are equal.
    result = field_value
    for (start, end) in zip(start_enclosure, end_enclosure):
        if start == end:
            result = result[1:-1]
        else:
            break

    # Check if braces are still correct.
    for x in range(5):
        braces_level = 0
        for char in result:
            if char == '{':
                braces_level += 1
            elif char == '}':
                braces_level -= 1
            if braces_level < 0:
                break

        if braces_level != 0:
            if x > 3:
                return field_value  # Give up on changing anything and just return the original value.
            result = "{" + result + "}"  # Add a pair of braces and hope it fixes the problem.
        else:
            break
    return result


def cleanup(bib_file: BibFile):
    config = json_loader.load_config()

    # Load values from config (or default values).
    convert_special_symbols = config.get("convert_special_symbols", False)
    url = config.get("use_url", True)
    doi = config.get("use_doi", True)
    comments = config.get("comments", True)
    comment_entries = config.get("comment_entries", True)
    lowercase_entry_types = config.get("lowercase_entry_types", False)
    lowercase_fields = config.get("lowercase_fields", False)
    braces_enclosure = config.get("braces_enclosure", False)
    quotation_marks_enclosure = config.get("quotation_marks_enclosure", False)

    fields = config.get("unnecessary_fields", [])

    if not comments:
        remove_comments(bib_file)
    if not comment_entries:
        remove_comment_entries(bib_file)

    for entry in bib_file.content:
        if isinstance(entry, Reference):
            remove_fields(entry, fields)
            clean_url_and_doi(entry, url, doi)
            if lowercase_entry_types:
                lower_entry_type(entry)
            if lowercase_fields:
                lower_fields(entry)
            if braces_enclosure and quotation_marks_enclosure:
                raise ValueError("Config file has invalid enclosures set, set only one to true.")
            if convert_special_symbols:
                convert_symbols(entry)
            if braces_enclosure:
                change_field_enclosure(entry, '{', '}')
            if quotation_marks_enclosure:
                change_field_enclosure(entry, '"', '"')

    return bib_file
