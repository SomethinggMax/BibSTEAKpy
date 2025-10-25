from bibsteak import api 

WORKDIR= "/abs/path/to/wd"
TARGET_FILES = ["master.bib", "workshop.bib"]
api.cwd(WORKDIR)
api.pwd(WORKDIR) # Print command
api.config.use_url(True) # Set values in the config this way

for f in api.list():
    if f.filename in TARGET_FILES:
        api.load(f)
        api.clean(f) 
        api.gr(f)
        api.ord(f, field='year')
    else:
        api.exp(f)
        api.filter(f, field='author', value='John') # Print command

api.mer(mode='-all', new_filename="merged_file.bib")




