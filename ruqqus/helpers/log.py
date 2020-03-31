from os import environ

def log(text, level=1):
    if int(environ.get("LOG_LEVEL",0)) >= level:
        print(text)
