import json


def _load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f) or {}
    except Exception:
        print(f"Failed to load {path}, returning empty dict.")
        return {}


def _dump_json(dictionary: dict, path, indent: int, ensure_ascii: bool):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(dictionary, file, indent=indent, ensure_ascii=ensure_ascii)


def load_config():
    return _load_json('config.json')


def dump_config(dictionary: dict):
    return _dump_json(dictionary, 'config.json', indent=2, ensure_ascii=True)


def get_working_directory_path():
    return load_config().get("working_directory")


def load_abbreviations():
    return _load_json('abbreviations.json')


def load_synonyms():
    return _load_json('synonyms.json')


def load_tags():
    return _load_json('tags.json')


def dump_synonyms(dictionary: dict):
    return _dump_json(dictionary, 'synonyms.json', indent=4, ensure_ascii=False)
