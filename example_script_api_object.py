from bibsteak import api

WD = "C:\\Users\\tabre\\Desktop\\storage"
TARGET_FILE = "example2.bib"
TARGET_FILES = ["example.bib", "example2.bib", "example3.bib"]

api.set_wd(WD)
api.list_names() # Retrieve all file names from the set working directory.
api.exp(TARGET_FILE)

for filename in TARGET_FILES:
    if api.search(filename, "John Lenonx"):
        api.ord(filename) # Sort in ascending order
    else:
        api.ord(filename, True) # Sord in descending order