from sqlalchemy import *
from teedee.classes.dbModels import _engine
metadata = MetaData()

def createTables():
    users = Table('users', metadata,
                  Column('id', BigInteger, primary_key=True),
                  Column('username', String(30), default=None),
                  Column('email', String(50), default=None),
                  Column('passhash', String(200), default=None),
                  Column('created_utc', BigInteger, default=0),
                  Column('is_activated', Boolean, default=False),
                  Column('is_admin', Boolean, default=False),
                  Column('is_mod', Boolean, default=False),
                  Column('is_banned', Boolean, default=False),
                  extend_existing=True,
                  mysql_engine='InnoDB',
                  mysql_charset='utf8')

    comments = Table('comments', metadata,
                     Column('id', BigInteger, primary_key=True),
                     Column('author_id', BigInteger, default=0),
                     Column('body', String(10000), default=None),
                     Column('parent_submission', BigInteger, default=0),
                     Column('parent_comment', BigInteger, default=0),
                     Column('created_utc', BigInteger, default=0),
                     Column('is_banned', Boolean, default=False),
                     extend_existing=True,
                     mysql_engine='InnoDB',
                     mysql_charset='utf8')

    submissions = Table('submissions', metadata,
                        Column('id', BigInteger, primary_key=True),
                        Column('author_id', BigInteger, default=0),
                        Column('title', String(500), default=None),
                        Column('url', String(500), default=None),
                        Column('created_utc', BigInteger, default=0),
                        Column('is_banned', Boolean, default=False),
                        extend_existing=True,
                        mysql_engine='InnoDB',
                        mysql_charset='utf8')

    metadata.create_all(_engine)

createTables()

