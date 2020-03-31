from os import environ

log_level=int(environ.get("LOG_LEVEL",0))

def log(text, level=1):
    if log_level >= level:
        print(text)
