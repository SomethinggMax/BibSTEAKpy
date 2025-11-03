import json
import os

CONFIG_TEMPLATE = {
    "abstract_strong_match": 0.9,
    "abstract_strong_mismatch": 0.5,
    "user_interface": "CLI",
    "working_directory": "",
    "add_abbreviations_as_strings": False,
    "remove_newlines_in_fields": False,
    "convert_special_symbols_to_unicode": True,
    "prefer_url_over_doi": False,
    "prefer_doi_over_url": True,
    "keep_comments": True,
    "keep_comment_entries": True,
    "lowercase_entry_types": False,
    "lowercase_fields": False,
    "change_enclosures_to_braces": False,
    "change_enclosures_to_quotation_marks": False,
    "unnecessary_fields": ["ee", "venue"],
}

# Get the directories relative to the  json_loader directory.
json_loader_directory = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(json_loader_directory, "../jsons/config.json")
TAGS_FILE = os.path.join(json_loader_directory, "../jsons/tags.json")
ABBREVIATIONS_FILE = os.path.join(json_loader_directory, "../jsons/abbreviations.json")
SYNONYMS_FILE = os.path.join(json_loader_directory, "../jsons/synonyms.json")


def _load_json(path):
    # error recovery: if file does not exist create it with empty json
    if not os.path.exists(path):
        _dump_json({}, path, 2, True)

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception as e:
        return {}


def _dump_json(dictionary: dict, path, indent: int, ensure_ascii: bool):
    with open(path, "w", encoding="utf-8") as file:
        file.seek(0)  # move pointer to first position
        json.dump(dictionary, file, indent=indent, ensure_ascii=ensure_ascii)
        file.truncate()  # remove all that comes after replaced text


def load_config():
    # error recovery: in case of deletion of file, dump template
    if _load_json(CONFIG_FILE) == {}:
        dump_config(CONFIG_TEMPLATE)
    return _load_json(CONFIG_FILE)


def dump_config(dictionary: dict):
    return _dump_json(dictionary, CONFIG_FILE, 2, True)


def get_wd_path():
    if not is_wd_path_set:
        raise Exception(f"working directory not set! Use cwd <absolute/path/to/directory> to set it")
    return load_config().get("working_directory")


def is_wd_path_set():
    wd_path = load_config().get("working_directory")
    return False if wd_path == "" else True


def load_abbreviations():
    return _load_json(ABBREVIATIONS_FILE)


def load_synonyms():
    return _load_json(SYNONYMS_FILE)


def load_tags():
    return _load_json(TAGS_FILE)


def dump_tags(dictionary: dict):
    return _dump_json(dictionary, TAGS_FILE, 2, True)


def dump_synonyms(dictionary: dict):
    return _dump_json(dictionary, SYNONYMS_FILE, 4, False)
