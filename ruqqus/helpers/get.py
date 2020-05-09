from .base36 import *
from ruqqus.__main__ import db
from ruqqus.classes import *

def get_user(username, graceful=False):

    x=db.query(User).filter(User.username.ilike(username)).first()
    if not x:
        if not graceful:
            abort(404)
        else:
            return None
    return x

def get_post(pid, v=None):

    i=base36decode(pid)

    if v:
        vt=db.query(Vote).filter_by(user_id=v.id, submission_id=i).subquery()


        items= db.query(Submission, vt.c.vote_type).filter(Submission.id==i).join(vt, isouter=True).first()
        
        x=items[0]
        x._voted=items[1] if items[1] else 0

    else:
        x=db.query(Submission).filter_by(id=i).first()

    if not x:
        abort(404)
    return x

def get_posts(pids, sort="hot", v=None):

    if v:
        vt=db.query(Vote).filter(Vote.user_id==v.id, Vote.submission_id.in_(pids)).subquery()


        posts= db.query(Submission, vt.c.vote_type).filter(Submission.id.in_(pids)).join(vt, isouter=True)

        if sort=="hot":
            posts=posts.order_by(Submission.score_hot.desc())
        elif sort=="new":
            posts=posts.order_by(Submission.created_utc.desc())
        elif sort=="disputed":
            posts=posts.order_by(Submission.score_disputed.desc())
        elif sort=="top":
            posts=posts.order_by(Submission.score_top.desc())
        elif sort=="activity":
            posts=posts.order_by(Submission.score_activity.desc())
        else:
            abort(422)

        items=[i for i in posts.all()]
        
        posts=[n[0] for n in items]
        for i in range(len(posts)):
            vote = items[i][1] if items[i][1] else 0
            posts[i]._voted = vote


    else:
        posts=db.query(Submission).filter(Submission.id.in_(pids))

        if sort=="hot":
            posts=posts.order_by(Submission.score_hot.desc())
        elif sort=="new":
            posts=posts.order_by(Submission.created_utc.desc())
        elif sort=="disputed":
            posts=posts.order_by(Submission.score_disputed.desc())
        elif sort=="top":
            posts=posts.order_by(Submission.score_top.desc())
        elif sort=="activity":
            posts=posts.order_by(Submission.score_activity.desc())
        else:
            abort(422)

        posts=[i for i in posts.all()]

    return posts

def get_post_with_comments(pid, sort_type="hot", v=None):

    post=get_post(pid, v=v)

    if v:
        votes=db.query(CommentVote).filter(CommentVote.user_id==v.id).subquery()

        comms=db.query(
            Comment,
            User,
            Title,
            votes.c.vote_type
            ).filter(
            Comment.parent_submission==post.id,
            Comment.level<=6
            ).join(Comment.author).join(
            User.title, isouter=True
            ).join(
            votes,
            votes.c.comment_id==Comment.id,
            isouter=True
            )

        if sort_type=="hot":
            comments=comms.order_by(Comment.score_hot.desc()).all()
        elif sort_type=="top":
            comments=comms.order_by(Comment.score_top.desc()).all()
        elif sort_type=="new":
            comments=comms.order_by(Comment.created_utc.desc()).all()
        elif sort_type=="disputed":
            comments=comms.order_by(Comment.score_disputed.desc()).all()
        elif sort_type=="random":
            c=comms.all()
            comments=random.sample(c, k=len(c))
        else:
            abort(422)


        output=[]
        for c in comms:
            comment=c[0]
            comment._title=c[2]
            comment._voted=c[3] if c[3] else 0
            output.append(comment)
        post._preloaded_comments=output

    else:
        comms=db.query(
            Comment,
            User,
            Title
            ).filter(
            Comment.parent_submission==post.id,
            Comment.level<=6
            ).join(Comment.author).join(
            User.title, isouter=True
            )

        if sort_type=="hot":
            comments=comms.order_by(Comment.score_hot.desc()).all()
        elif sort_type=="top":
            comments=comms.order_by(Comment.score_top.desc()).all()
        elif sort_type=="new":
            comments=comms.order_by(Comment.created_utc.desc()).all()
        elif sort_type=="disputed":
            comments=comms.order_by(Comment.score_disputed.desc()).all()
        elif sort_type=="random":
            c=comms.all()
            comments=random.sample(c, k=len(c))
        else:
            abort(422)

        output=[]
        for c in comms:
            comment=c[0]
            comment._title=c[2]
            output.append(comment)

        post._preloaded_comments=output

    return post


def get_comment(cid, v=None):

    i=base36decode(cid)

    if v:
        vt=db.query(CommentVote).filter(CommentVote.user_id==v.id, CommentVote.comment_id==i).subquery()


        items= db.query(Comment, vt.c.vote_type).filter(Comment.id==i).join(vt, isouter=True).first()
        
        x=items[0]
        x._voted=items[1] if items[1] else 0

    else:
        x=db.query(Comment).filter_by(id=i).first()

    if not x:
        abort(404)
    return x

def get_comments(cids, v=None):

    if v:
        vt=db.query(CommentVote).filter(CommentVote.user_id==v.id, CommentVote.comment_id.in_(cids)).subquery()


        items= db.query(Comment, vt.c.vote_type).filter(Comment.id.in_(cids)).join(vt, isouter=True).all()

        items=[i for i in items]
        output=[]
        for i in items:
        
            x=i[0]
            x._voted=i[1] if i[1] else 0
            output.append(x)

    else:
        x=db.query(Comment).filter(Comment.id.in_(cids)).all()
        output=[i for i in x]

    
    return output

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

def get_domain(s):

    #parse domain into all possible subdomains
    parts=s.split(".")
    domain_list=set([])
    for i in range(len(parts)):
        new_domain=parts[i]
        for j in range(i+1, len(parts)):
            new_domain+="."+parts[j]

        domain_list.add(new_domain)

    domain_list=tuple(list(domain_list))

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


def get_mod(uid, bid):

    mod=db.query(ModRelationship).filter_by(board_id=bid,
                                            user_id=uid,
                                            accepted=True,
                                            invite_rescinded=False).first()

    return mod
