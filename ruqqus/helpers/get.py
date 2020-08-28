from .base36 import *
from .sqla_values import *
from ruqqus.classes import *
from flask import g
from sqlalchemy.orm import joinedload

import re

def get_user(username, v=None, nSession=None, graceful=False):

    username=username.replace('\\','')
    username=username.replace('_', '\_')

    if not nSession:
        nSession=g.db
        

    user=nSession.query(User
        ).filter(
        User.username.ilike(username)
        ).first()

    if not user:
        if not graceful:
            abort(404)
        else:
            return None

    if v:
        block=nSession.query(UserBlock).filter(
            or_(
                and_(
                    UserBlock.user_id==v.id, 
                    UserBlock.target_id==user.id
                    ),
                and_(UserBlock.user_id==user.id,
                    UserBlock.target_id==v.id
                    )
                )
            ).first()

        user._is_blocking=block and block.user_id==v.id
        user._is_blocked=block and block.target_id==v.id

    return user

def get_post(pid, v=None, graceful=False, nSession=None, **kwargs):

    if isinstance(pid, str):
        i=base36decode(pid)
    else:
        i=pid
        
    nSession=nSession or kwargs.get("session")or g.db

    if v:
        vt=nSession.query(Vote).filter_by(user_id=v.id, submission_id=i).subquery()
        mod=nSession.query(ModRelationship).filter_by(user_id=v.id, invite_rescinded=False).subquery()
        boardblocks=nSession.query(BoardBlock).filter_by(user_id=v.id).subquery()
        blocking=v.blocking.subquery()


        items= nSession.query(
                Submission, 
                vt.c.vote_type, 
                mod.c.id,
                boardblocks.c.id,
                blocking.c.id
            ).options(
            joinedload(Submission.author).joinedload(User.title)
            ).filter(Submission.id==i
            ).join(vt, vt.c.submission_id==Submission.id, isouter=True
            ).join(mod, mod.c.board_id==Submission.board_id, isouter=True
            ).join(boardblocks, boardblocks.c.board_id==Submission.board_id, isouter=True
            ).join(blocking, blocking.c.target_id==Submission.author_id, isouter=True
            ).first()
        
        if not items:
            abort(404)
        
        x=items[0]
        x._voted=items[1] or 0
        x._is_guildmaster=items[2] or 0
        x._is_blocking_guild=items[3] or 0
        x._is_blocking=items[4] or 0

    else:
        x=nSession.query(Submission).options(
            joinedload(Submission.author).joinedload(User.title)
            ).filter(Submission.id==i).first()

    if not x and not graceful:
        abort(404)
    return x

def get_posts(pids, sort="hot", v=None):

    

    if not pids:
        return []

    queries=[]

    if v:
        for pid in pids:
            
            vt=g.db.query(Vote).filter_by(submission_id=pid, user_id=v.id).subquery()
            mod=g.db.query(ModRelationship).filter_by(user_id=v.id, invite_rescinded=False).subquery()
            boardblocks=g.db.query(BoardBlock).filter_by(user_id=v.id).subquery()
            blocking=v.blocking.subquery()
            blocked=v.blocked.subquery()
            subs=v.subscriptions.filter_by(is_active=True).subquery()

            query=g.db.query(
                    Submission,
                    vt.c.vote_type, 
                    mod.c.id, 
                    boardblocks.c.id,
                    blocking.c.id,
                    blocked.c.id,
                    subs.c.id
                ).options(joinedload(Submission.author).joinedload(User.title)
                ).filter_by(id=pid
                ).join(vt, vt.c.submission_id==Submission.id, isouter=True
                ).join(mod, mod.c.board_id==Submission.board_id, isouter=True
                ).join(boardblocks, boardblocks.c.board_id==Submission.board_id, isouter=True
                ).join(blocking, blocking.c.target_id==Submission.author_id, isouter=True
                ).join(blocked, blocked.c.user_id==Submission.author_id, isouter=True
                ).join(subs, subs.c.board_id==Submission.board_id, isouter=True
                )
            queries.append(query)

        queries=tuple(queries)
        first_query=queries[0]
        if len(queries) > 1:
            other_queries=queries[1:len(queries)]
        else:
            other_queries=tuple()

        posts=first_query.union_all(*other_queries).order_by(None).all()

        output=[p[0] for p in posts]
        for i in range(len(output)):
            output[i]._voted=posts[i][1] or 0
            output[i]._is_guildmaster=posts[i][2] or 0
            output[i]._is_blocking_guild=posts[i][3] or 0
            output[i]._is_blocking=posts[i][4] or 0
            output[i]._is_blocked=posts[i][5] or 0
            output[i]._is_subscribed=posts[i][6] or 0
    else:
        for pid in pids:
            query=g.db.query(Submission
                ).options(joinedload(Submission.author).joinedload(User.title)
                ).filter_by(id=pid
                )
            queries.append(query)

        queries=tuple(queries)
        first_query=queries[0]
        if len(queries) > 1:
            other_queries=queries[1:len(queries)]
        else:
            other_queries=tuple()
        output=first_query.union_all(*other_queries).order_by(None).all()

    return output

def get_post_with_comments(pid, sort_type="top", v=None):

    post=get_post(pid, v=v)

    if v:
        votes=g.db.query(CommentVote).filter_by(user_id=v.id).subquery()

        blocking=v.blocking.subquery()

        blocked=v.blocked.subquery()

        comms=g.db.query(
            Comment,
            votes.c.vote_type,
            blocking.c.id,
            blocked.c.id
            ).options(
            joinedload(Comment.author).joinedload(User.title)
            ).filter(
            Comment.parent_submission==post.id,
            Comment.level<=6
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
            comment._voted=c[1] or 0
            comment._is_blocking=c[2] or 0
            comment._is_blocked=c[3] or 0
            output.append(comment)
        post._preloaded_comments=output

    else:
        comms=g.db.query(
            Comment
            ).options(
            joinedload(Comment.author).joinedload(User.title)
            ).filter(
            Comment.parent_submission==post.id,
            Comment.level<=6
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

        output=[c for c in comments]

        post._preloaded_comments=output

    return post


def get_comment(cid, nSession=None, v=None, graceful=False, **kwargs):


    if isinstance(cid, str):
        i=base36decode(cid)
    else:
        i=cid

    nSession = nSession or kwargs.get('session') or g.db

    if v:
        blocking=v.blocking.subquery()
        blocked=v.blocked.subquery()
        vt=g.db.query(CommentVote).filter(CommentVote.user_id==v.id, CommentVote.comment_id==i).subquery()


        items= g.db.query(Comment, vt.c.vote_type).options(
            joinedload(Comment.author).joinedload(User.title)
            ).filter(
            Comment.id==i
            ).join(
            vt, vt.c.comment_id==Comment.id, isouter=True
            ).first()
        
        if not items:
            abort(404)

        x=items[0]
        x._voted=items[1] or 0

        block=nSession.query(UserBlock).filter(
            or_(
                and_(
                    UserBlock.user_id==v.id, 
                    UserBlock.target_id==x.author_id
                    ),
                and_(UserBlock.user_id==x.author_id,
                    UserBlock.target_id==v.id
                    )
                )
            ).first()


        x._is_blocking=block and block.user_id==v.id
        x._is_blocked=block and block.target_id==v.id

    else:
        x=g.db.query(Comment).options(
            joinedload(Comment.author).joinedload(User.title)
            ).filter(Comment.id==i).first()

    if not x and not graceful:
        abort(404)
    return x

def get_comments(cids, v=None, nSession=None, sort_type="new", load_parent=False, **kwargs):

    #output= [get_comment(cid, v=v, graceful=True, nSession=nSession) for cid in cids]
    #return [i for i in output if i]

    if not cids:
        return []

    nSession=nSession or kwargs.get('session') or g.db

    queries=[]

    if v:
        for cid in cids:
            vt=nSession.query(CommentVote).filter_by(comment_id=cid, user_id=v.id).subquery()
            query=nSession.query(Comment, vt.c.vote_type
                ).options(joinedload(Comment.author).joinedload(User.title)
                )
            if load_parent:
                query=query.options(joinedload(Comment.parent_comment).joinedload(Comment.author).joinedload(User.title))
            query=query.filter_by(id=cid
                ).join(
                vt,
                vt.c.comment_id==Comment.id,
                isouter=True
                )

            queries.append(query)
        queries=tuple(queries)
        first_query=queries[0]
        if len(queries) > 1:
            other_queries=queries[1:len(queries)]
        else:
            other_queries=tuple()
        comments=first_query.union_all(*other_queries).order_by(None).all()

        output=[x[0] for x in comments]
        for i in range(len(output)):
            output[i]._voted=comments[i][1] or 0
    else:
        for cid in cids:
            query=nSession.query(Comment
                ).options(joinedload(Comment.author).joinedload(User.title)
                ).filter_by(id=cid
                )
            queries.append(query)

        queries=tuple(queries)
        first_query=queries[0]
        if len(queries) > 1:
            other_queries=queries[1:len(queries)]
        else:
            other_queries=tuple()
        output=first_query.union_all(*other_queries).order_by(None).all()

    return output
    

def get_board(bid, graceful=False):

    x=g.db.query(Board).options(joinedload(Board.moderators).joinedload(ModRelationship.user)).filter_by(id=base36decode(bid)).first()
    if not x:
        if graceful:
            return None
        else:
            abort(404)
    return x

def get_guild(name, graceful=False):

    name=name.lstrip('+')

    name=name.replace('\\', '')
    name=name.replace('_','\_')

    x=g.db.query(Board).options(joinedload(Board.moderators).joinedload(ModRelationship.user)).filter(Board.name.ilike(name)).first()
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

def get_application(client_id, graceful=False):

    application = g.db.query(OauthApp).filter_by(client_id=client_id).first()
    if not application and not graceful:
        abort(404)

    return application

def get_from_permalink(link, v=None):

    if "@" in link:

        name=re.search("/@(\w+)", link).match(1)
        return get_user(name)

    if "+" in link:

        name=re.search("/\+(\w+)", link).match(1)
        return get_guild(name)

    ids=re.search("://[^/]+/post/(\w+)/[^/]+(/(\w+))?", link)

    post_id=ids.group(1)
    comment_id=ids.group(3)

    if comment_id:
        return get_comment(comment_id, v=v)

    else:
        return get_post(post_id, v=v)