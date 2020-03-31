from os import environ

def log(text, level=1):
    if environ.get("LOG_LEVEL",0) >= level:
        print(text)
