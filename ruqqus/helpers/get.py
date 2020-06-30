from .base36 import *
from ruqqus.classes import *
from flask import g

def get_user(username, v=None, session=None, graceful=False):

    username=username.replace('\\','')
    username=username.replace('_', '\_')

    if not session:
        session=g.db

    if v:
        blocking=v.blocking.subquery()
        blocked=v.blocked.subquery()

        q=session.query(User, blocking.c.id, blocked.c.id
            ).filter(
            User.username.ilike(username)
            ).join(
            blocking,
            blocking.c.target_id==User.id,
            isouter=True
            ).join(
            blocked,
            blocked.c.user_id==User.id,
            isouter=True
            ).first()

        if not q:
            if not graceful:
                abort(404)
            else:
                return None

        #print(q)
        x=q[0]
        x._is_blocking=q[1] or 0
        x._is_blocked=q[2] or 0
    else:
        x=session.query(User).filter(User.username.ilike(username)).first()
        if not x:
            if not graceful:
                abort(404)
            else:
                return None
    return x

def get_post(pid, v=None, session=None):

    i=base36decode(pid)
    
    if not session:
        session=g.db

    if v:
        vt=session.query(Vote).filter_by(user_id=v.id, submission_id=i).subquery()


        items= session.query(Submission, User, vt.c.vote_type
            ).filter(Submission.id==i).join(Submission._author).join(vt, isouter=True).first()
        
        if not items:
            abort(404)
        
        x=items[0]
        x.author=items[1]
        x._voted=items[2] or 0

    else:
        row=session.query(Submission, User).join(Submission._author).filter(Submission.id==i).first()
        x=row[0]
        x.author=row[1]

    if not x:
        abort(404)
    return x

def get_posts(pids, sort="hot", v=None):

    if v:
        vt=g.db.query(Vote).filter(Vote.user_id==v.id, Vote.submission_id.in_(pids)).subquery()


        posts= g.db.query(Submission, User, Title, vt.c.vote_type).filter(
            Submission.id.in_(pids)
            ).join(
            Submission._author
            ).join(
            User.title, isouter=True
            ).join(
            vt, vt.c.submission_id==Submission.id, isouter=True
            )

        items=[i for i in posts.all()]

        
        posts=[n[0] for n in items]
        for i in range(len(posts)):
            posts[i].author=items[i][1]
            posts[i]._title=items[i][2]
            posts[i]._voted=items[i][3] or 0




    else:
        posts=g.db.query(Submission, User, Title).filter(
            Submission.id.in_(pids)
            ).join(
            Submission._author
            ).join(
            User.title, isouter=True
            )


        items=[i for i in posts.all()]
        
        posts=[n[0] for n in items]
        for i in range(len(posts)):
            posts[i].author=items[i][1]
            posts[i]._title=items[i][2]

    posts=sorted(posts, key= lambda x: pids.index(x.id))
    return posts

def get_post_with_comments(pid, sort_type="top", v=None):

    post=get_post(pid, v=v)

    if v:
        votes=g.db.query(CommentVote).filter_by(user_id=v.id).subquery()

        blocking=v.blocking.subquery()

        blocked=v.blocked.subquery()

        comms=g.db.query(
            Comment,
            User,
            Title,
            votes.c.vote_type,
            blocking.c.id,
            blocked.c.id
            ).filter(
            Comment.parent_submission==post.id,
            Comment.level<=6
            ).join(Comment._author).join(
            User.title,
            isouter=True
            ).join(
            votes,
            votes.c.comment_id==Comment.id,
            isouter=True
            ).join(
            blocking,
            blocking.c.target_id==Comment.author_id,
            isouter=True
            ).join(
            blocked,
            blocked.c.user_id==Comment.author_id,
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
        for c in comments:
            comment=c[0]
            comment.author=c[1]
            comment._title=c[2]
            comment._voted=c[3] or 0
            comment._is_blocking=c[4] or 0
            comment._is_blocked=c[5] or 0
            output.append(comment)
        post._preloaded_comments=output

    else:
        comms=g.db.query(
            Comment,
            User,
            Title
            ).filter(
            Comment.parent_submission==post.id,
            Comment.level<=6
            ).join(Comment._author).join(
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
        for c in comments:
            comment=c[0]
            comment.author=c[1]
            comment._title=c[2]
            output.append(comment)

        post._preloaded_comments=output

    return post


def get_comment(cid, v=None):


    if isinstance(cid, str):
        i=base36decode(cid)
    else: i=cid



    if v:
        blocking=v.blocking.subquery()
        blocked=v.blocked.subquery()
        vt=g.db.query(CommentVote).filter(CommentVote.user_id==v.id, CommentVote.comment_id==i).subquery()


        items= g.db.query(Comment, User, vt.c.vote_type, blocking.c.id, blocked.c.id).filter(
            Comment.id==i
            ).join(
            Comment._author
            ).join(
            vt, isouter=True
            ).join(
            blocking,
            blocking.c.target_id==Comment.author_id,
            isouter=True
            ).join(
            blocked,
            blocked.c.user_id==Comment.author_id,
            isouter=True
            ).first()
        
        if not items:
            abort(404)
        x=items[0]
        x.author=items[1]
        x._voted=items[2] or 0
        x._is_blocking=items[3] or 0
        x._is_blocked=items[4] or 0

    else:
        items=g.db.query(Comment, User).filter(Comment.id==i).join(Comment._author).first()
        x=items[0]
        x.author=items[1]

    if not x:
        abort(404)
    return x

def get_comments(cids, v=None, session=None, sort_type="new"):

    if not session:
        session=g.db

    if v:
        blocking=v.blocking.subquery()
        blocked=v.blocked.subquery()
        vt=session.query(CommentVote).filter(CommentVote.user_id==v.id, CommentVote.comment_id.in_(cids)).subquery()


        items= session.query(Comment, User, vt.c.vote_type, blocking.c.id, blocked.c.id).filter(
            Comment.id.in_(cids)
            ).join(
            Comment._author
            ).join(
            vt, 
            isouter=True
            ).join(
            blocking,
            blocking.c.target_id==Comment.author_id,
            isouter=True
            ).join(
            blocked,
            blocked.c.user_id==Comment.author_id,
            isouter=True
            ).order_by(Comment.created_utc.desc()).all()

        output=[]
        for i in items:
        
            x=i[0]
            x.author=i[1]
            x._voted=i[2] or 0
            x._is_blocking=i[3] or 0
            x._is_blocked=i[4] or 0
            output.append(x)

    else:
        entries=session.query(Comment, User).join(Comment._author).filter(Comment.id.in_(cids)).all()
        output=[]
        for row in entries:
            comment=row[0]
            comment.author=row[1]
            output.append(comment)

    output=sorted(output, key=lambda x:cids.index(x.id))
    
    return output

def get_board(bid):

    x=g.db.query(Board).filter_by(id=base36decode(bid)).first()
    if not x:
        abort(404)
    return x

def get_guild(name, graceful=False):

    name=name.lstrip('+')

    name=name.replace('\\', '')
    name=name.replace('_','\_')

    x=g.db.query(Board).filter(Board.name.ilike(name)).first()
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

    doms=[x for x in g.db.query(Domain).filter(Domain.domain.in_(domain_list)).all()]

    if not doms:
        return None

    #return the most specific domain - the one with the longest domain property
    doms= sorted(doms, key=lambda x: len(x.domain), reverse=True)

    return doms[0]

def get_title(x):

    title=g.db.query(Title).filter_by(id=x).first()

    if not title:
        abort(400)

    else:
        return title


def get_mod(uid, bid):

    mod=g.db.query(ModRelationship).filter_by(board_id=bid,
                                            user_id=uid,
                                            accepted=True,
                                            invite_rescinded=False).first()

    return mod
