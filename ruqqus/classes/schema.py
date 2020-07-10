import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from ruqqus.classes import Board as BoardModel#, User as UserModel

class Board(SQLAlchemyObjectType):
    class Meta:
        model = BoardModel
        interfaces = (relay.Node, )


"""class User(SQLAlchemyObjectType):
    class Meta:
        model = UserModel
        interfaces = (relay.Node, )"""


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    # Allows sorting over multiple columns, by default over the primary key
    #all_submissions = SQLAlchemyConnectionField(User.connection)
    # Disable sorting over this field
    all_boards = SQLAlchemyConnectionField(Board.connection, sort=None)

schema = graphene.Schema(query=Query)