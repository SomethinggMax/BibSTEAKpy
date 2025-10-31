import json
import os

CONFIG_TEMPLATE = {
    "abstract_strong_match": 0.9,
    "abstract_strong_mismatch": 0.5,
    "user_interface": "CLI",
    "working_directory": "",
    "remove_newlines_in_fields": False,
    "convert_special_symbols_to_unicode": True,
    "prefer_url": False,
    "prefer_doi": True,
    "keep_comments": True,
    "keep_comment_entries": True,
    "lowercase_entry_types": False,
    "lowercase_fields": False,
    "change_enclosures_to_braces": False,
    "change_enclosures_to_quotation_marks": False,
    "unnecessary_fields": ["ee", "venue"],
}
CONFIG_FILE = "jsons/config.json"
TAGS_FILE = "jsons/tags.json"
ABBREVIATIONS_FILE = "jsons/abbreviations.json"
SYNONYMS_FILE = "jsons/synonyms.json"


def _load_json(path):
    #error recovery: if file does not exist create it with empty json
    if not os.path.exists(path):
        _dump_json({}, path, 2, True)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f) or {}


def _dump_json(dictionary: dict, path, indent: int, ensure_ascii: bool):
    with open(path, "w", encoding="utf-8") as file:
        file.seek(0) #move pointer to first position
        json.dump(dictionary, file, indent, ensure_ascii)
        file.truncate() #remove all that comes after replaced text


def load_config():
    #error recovery: in case of deletion of file, dump template
    if _load_json(CONFIG_FILE) == {}:
        dump_config(CONFIG_TEMPLATE)
    return _load_json(CONFIG_FILE)


def dump_config(dictionary: dict):
    return _dump_json(dictionary, CONFIG_FILE, 2, True)


def get_wd_path():
    wd_path = load_config().get("working_directory")
    if wd_path == "":
        raise Exception(f"working directory not set! Use cwd <absolute/path/to/directory> to set it")
    return wd_path


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
