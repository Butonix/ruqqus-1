from ruqqus.classes import *
from .base36 import *
from ruqqus.__main__ import db

def get_user(username, graceful=False):

    x=db.query(User).filter(User.username.ilike(username)).first()
    if not x:
        if not graceful:
            abort(404)
        else:
            return None
    return x

def get_post(pid):

    x=db.query(Submission).filter_by(id=base36decode(pid)).first()
    if not x:
        abort(404)
    return x

def get_comment(cid):

    x=db.query(Comment).filter_by(id=base36decode(cid)).first()
    if not x:
        abort(404)
    return x

def get_board(bid):

    x=db.query(Board).filter_by(id=base36decode(bid)).first()
    if not x:
        abort(404)
    return x

def get_guild(name, graceful=False):

    name=name.lstrip('+')

    x=db.query(Board).filter(Board.name.ilike(name)).first()
    if not x:
        if not graceful:
            abort(404)
        else:
            return None
    return x

def get_domain(domain):

    #parse domain into all possible subdomains
    parts=domain.split(".")
    domain_list=set([])
    for i in range(len(parts)):
        new_domain=parts[i]
        for j in range(i+1, len(parts)):
            new_domain+="."+parts[j]

            domain_list.add(new_domain)

    domain_list=list(domain_list)

    doms=[x for x in db.query(Domain).filter(Domain.domain.in_(domain_list)).all()]

    if not doms:
        return None

    #return the most specific domain - the one with the longest domain property
    doms= sorted(doms, key=lambda x: len(x.domain), reverse=True)

    return doms[0]

def get_title(x):

    title=db.query(Title).filter_by(id=x).first()

    if not title:
        abort(400)

    else:
        return title
