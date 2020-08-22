import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from ruqqus.classes import Board as BoardModel, User as UserModel, Submission as SubmissionModel, \
    SubmissionAux as SubmissionAuxModel, Comment as CommentModel, CommentAux as CommentAuxModel
#from ruqqus.classes import Board, User, Submission, SubmissionAux, Comment, CommentAux
from ruqqus.__main__ import app, Base, db_session
from flask_graphql import GraphQLView


class CommentGQL(SQLAlchemyObjectType):
    class Meta:
        model = SubmissionModel
        # abstract = True
        interfaces = (relay.Node,)
        exclude_fields = (
            'creation_ip'
        )

    comments_aux = graphene.List(lambda: CommentAuxGQL, id=graphene.String())

    def resolve_comments_aux(self, info, **kwargs):
        query = CommentAuxGQL.get_query(info)
        # query1 = Submission.get_query(info).first()
        query.filter_by(id=self.id).first()
        return query.filter_by(id=self.id).all()

    def resolve_submission(self, info, **kwargs):
        return CommentGQL.filter_by(is_banned=False,
                                      is_deleted=False).all()

class CommentAuxGQL(SQLAlchemyObjectType):
    class Meta:
        model = CommentAuxModel
        interfaces = (relay.Node,)

    # comments_aux = graphene.List(lambda: Comm, id=graphene.String())
    def resolve_comment_aux(self, info, **kwargs):
        # query = SubmissionAux.get_query(info)
        # return query.filter_by(id=kwargs['id']).all()
        return CommentAuxGQL.all()


class SubmissionGQL(SQLAlchemyObjectType):
    class Meta:
        model = SubmissionModel
        # abstract = True
        interfaces = (relay.Node,)
        exclude_fields = (
            'creation_ip'
        )
    posts_aux = graphene.List(lambda: SubmissionAuxGQL, id=graphene.String())

    def resolve_posts_aux(self, info, **kwargs):
        query = SubmissionAuxGQL.get_query(info)
        return query.filter_by(id=self.id).all()

    def resolve_submission(self, info, **kwargs):
        return SubmissionGQL.filter_by(is_banned=False,
                                         is_deleted=False,
                                         is_public=True).all()


class SubmissionAuxGQL(SQLAlchemyObjectType):
    class Meta:
        model = SubmissionAuxModel
        interfaces = (relay.Node,)

    # posts_aux = graphene.List(lambda: SubmissionAux, id=graphene.String())

    def resolve_submission_aux(self, info, **kwargs):
        # query = SubmissionAux.get_query(info)
        # return query.filter_by(id=kwargs['id']).all()
        return SubmissionAuxGQL.all()


class UserGQL(SQLAlchemyObjectType):
    class Meta:
        model = UserModel
        interfaces = (relay.Node,)

        # can use only one
        # 'only_fields' or 'exclude_fields'

        # only_fields = ('username', 'id','created_utc','admin_level','over_18')
        exclude_fields = (
            'passhash',
            'mfa_secret',
            'email',
            'delete_reason',
            'reddit_username',
            'patreon_id',
            'patreon_pledge_cents',
            'patreon_name',
            'patreon_access_token',
            'patreon_refresh_token'
        )

    posts = graphene.List(lambda: SubmissionGQL,
                          sort=graphene.String(),
                          page=graphene.Int()
                          )
    comments = graphene.List(lambda: CommentGQL,
                             sort=graphene.String(),
                             page=graphene.Int())

    def resolve_posts(self, info, **kwargs):
        sort = "hot"
        page = 1
        if 'page' in kwargs:
            page = kwargs['page']

        query = SubmissionGQL.get_query(info)
        query = query.filter_by(is_banned=False, is_deleted=False)

        if self.id:
            query = query.filter_by(author_id=self.id)
        query = query.join(UserModel, SubmissionModel.author_id)

        if 'sort' in kwargs:
            sort = kwargs['sort']

        if sort == "hot":
            query = query.order_by(SubmissionModel.score_hot.desc())
        elif sort == "new":
            query = query.order_by(SubmissionModel.created_utc.desc())
        elif sort == "disputed":
            query = query.order_by(SubmissionModel.score_disputed.desc())
        elif sort == "top":
            query = query.order_by(SubmissionModel.score_top.desc())
        elif sort == "activity":
            query = query.order_by(SubmissionModel.score_activity.desc())

        if 'id' in kwargs:
            query = query.filter_by(id=kwargs['id'])  # \
            # .filter(Submission.author_id == kwargs['id'])

        query = query.join(SubmissionAuxModel, SubmissionAuxModel.id==SubmissionModel.id)

        if 'title' in kwargs:
            query = query.filter(SubmissionAuxModel.title == kwargs['title'])

        return query.offset(25 * (page - 1)).limit(26).all()


    def resolve_comments(self, info, **kwargs):
        page = 1
        if 'page' in kwargs:
            page = kwargs['page']

        query = CommentGQL.get_query(info)
        query = query.filter_by(is_banned=False, is_deleted=False)

        if self.id:
            query = query.filter_by(author_id=self.id)

        if 'sort' in kwargs:
            sort = kwargs['sort']
            if sort == "hot":
                query = query.order_by(CommentModel.score_hot.desc())
            elif sort == "new":
                query = query.order_by(CommentModel.created_utc.desc())
            elif sort == "disputed":
                query = query.order_by(CommentModel.score_disputed.desc())
            elif sort == "top":
                query = query.order_by(CommentModel.score_top.desc())


        if 'id' in kwargs:
            query = query.filter_by(id=kwargs['id'])
        query = query.join(CommentAuxModel, CommentModel.author_id==self.id)

        return query.offset(25 * (page - 1)).limit(26).all()


class GuildGQL(SQLAlchemyObjectType):
    class Meta:
        model = BoardModel
        interfaces = (relay.Node,)

    def resolve_guilds(self, info, **kwargs):
        return GuildGQL.fitler_by(is_private=False,
                                    is_banned=False
                                    ).all()

    posts = graphene.List(lambda: SubmissionGQL,
                          id=graphene.String(),
                          sort=graphene.String(),
                          title=graphene.String(),
                          page=graphene.Int()
                          )

    def resolve_posts(self, info, **kwargs):

        page = 1
        if 'page' in kwargs:
            page = kwargs['page']

        query = SubmissionGQL.get_query(info)
        query = query.filter_by(is_banned=False, is_deleted=False)

        if self.id:
            query = query.filter_by(board_id=self.id)

        if 'sort' in kwargs:
            sort = kwargs['sort']
            if sort == "hot":
                query = query.order_by(SubmissionModel.score_hot.desc())
            elif sort == "new":
                query = query.order_by(SubmissionModel.created_utc.desc())
            elif sort == "disputed":
                query = query.order_by(SubmissionModel.score_disputed.desc())
            elif sort == "top":
                query = query.order_by(SubmissionModel.score_top.desc())
            elif sort == "activity":
                query = query.order_by(SubmissionModel.score_activity.desc())

        if 'id' in kwargs:
            query = query.filter_by(id=kwargs['id'])

        query = query.join(SubmissionAuxModel, SubmissionModel.id==SubmissionAuxModel.id)

        if 'title' in kwargs:
            query = query.filter(SubmissionAuxModel.title == kwargs['title'])

        return query.offset(25*(page-1)).limit(26).all()




# all_users = SQLAlchemyConnectionField(User.connection)
# all_posts = SQLAlchemyConnectionField(Submission.connection, sort=None)

class Query(graphene.ObjectType):
    node = relay.Node.Field()
    # Allows sorting over multiple columns, by default over the primary key
    guild = SQLAlchemyConnectionField(GuildGQL.connection,
                                      id=graphene.String(),
                                      name=graphene.String()
                                      )

    user = SQLAlchemyConnectionField(UserGQL.connection,
                                     id=graphene.String(),
                                     username=graphene.String(),
                                     sort=graphene.String()
                                     )

    def resolve_guild(self, info, **kwargs):

        query = GuildGQL.get_query(info)

        if 'id' in kwargs:
            # print("id = ", kwargs['id'])
            query = query.filter_by(id=kwargs['id'])

        if 'name' in kwargs:
            query = query.filter_by(name=kwargs['name'])

        #if 'sort' in kwargs:
            #query

        return query.filter_by(is_private=False,
                               is_banned=False)


    def resolve_user(self, info, **kwargs):
        query = UserGQL.get_query(info)

        if 'id' in kwargs:
            # print("id = ", kwargs['id'])
            query = query.filter_by(id=kwargs['id'])

        if 'username' in kwargs:
            query = query.filter_by(username=kwargs['username'])

        return query.filter_by(is_private=False,
                               is_banned=0,
                               is_deleted=False)






schema = graphene.Schema(query=Query)


"""check = query.filter_by(id=kwargs['id'], is_private=True).all()
            if check:
                return ['private user']"""
"""submission_aux = SQLAlchemyConnectionField(SubmissionAux.connection, sort=None)
    def resolve_submission_aux(self, info, **kwargs):
        if "id" in kwargs:
            # print("uname = ", kwargs['id'])
            query = SubmissionAux.get_query(info)
            return query.filter_by(id=kwargs['id']).all()"""
