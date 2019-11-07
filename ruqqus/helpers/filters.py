import yaml
from flask import *
from os import environ
from urllib.parse import urlparse
from ruqqus.classes import Domain
from ruqqus.__main__ import db, app

def filter_post(url):

    domain=urlparse(url).netloc

    #parse domain into all possible subdomains
    parts=domain.split(".")
    domains=[]
    for i in range(len(parts)):
        new_domain=parts[i]
        for j in range(i+1, len(parts)):
            new_domain+="."+parts[j]

        domains.append(new_domain)
        

    #search db for options
    
    ban=db.query(Domain).filter(Domain.domain.in_(domains)).first()

    if ban:
        reasons=['',
                 "URL shorteners are not permitted."
                 ]
        return reasons[ban.reason]
    else:
        return False


