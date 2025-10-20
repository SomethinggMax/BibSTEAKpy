import json

def open_synonyms_file():
    with open('synonyms.json', 'r', encoding='utf-8') as f:
        synonyms = json.load(f)
    return synonyms

def replace_synonym(text: str) -> str | None:
    synonyms = open_synonyms_file()
    text = text.strip().strip("{}")   # remove whitespace and curly braces if needed
    for key, values in synonyms.items():
        if text == key or text in values:
            return key 
    return None

def add_synonyms(synonym_rules: dict) -> None:
    synonym_list = open_synonyms_file()
    for key in synonym_rules:
        syn_key = replace_synonym(key)
        if syn_key != None:
            for value in synonym_rules[key]:
                if value not in synonym_list[syn_key]:
                    synonym_list[syn_key].append(value)

    for key, values in synonym_rules.items():
        if replace_synonym(key) != None:
            continue
        if key in synonym_list:
            for value in values:
                if replace_synonym(value) != None:
                    continue
                if value not in synonym_list[key]:
                    synonym_list[key].append(value)
        else:
            synonym_list[key] = values
    with open('synonyms.json', 'w', encoding='utf-8') as f:
        json.dump(synonym_list, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    new_synonyms = {
        "P Visser": ["Visser, Pepijn", "Pepijn Visser"],
        "John Doe": ["Doe J", "J. Doe", "Doe, J."]
    }
    add_synonyms(new_synonyms)