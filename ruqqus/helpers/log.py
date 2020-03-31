from os import environ

log_level=environ.get("LOG_LEVEL")

def log(text, level=1):
    if log_level >= level:
        print(text)
