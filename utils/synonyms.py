import json

def open_synonyms_file():
    with open('synonyms.json', 'r', encoding='utf-8') as f:
        synonyms = json.load(f)
    return synonyms

def replace_synonym(text: str) -> str|None:
    synonyms = open_synonyms_file()
    for key, values in synonyms.items():
        if text in values or text == key:
            return key
    return None

def add_synonyms(synonym_rules: dict) -> None:
    synonym_list = open_synonyms_file()
    for key, values in synonym_rules.items():
        if key in synonym_list:
            for value in values:
                if value not in synonym_list[key]:
                    synonym_list[key].append(value)
        else:
            synonym_list[key] = values
    with open('synonyms.json', 'w', encoding='utf-8') as f:
        json.dump(synonym_list, f, indent=4, ensure_ascii=False)
