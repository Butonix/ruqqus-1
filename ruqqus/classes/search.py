import re
regex_user = "\W*(user:@([^\s]+)|user:([^\s]+))\W*"
regex_guild = "\W*(guild:\+([^\s]+)|guild:([^\s]+))\W*"
regex_title = "\W*(title:)\W*"

class Search:

    def __init__(self, query, session):
        self.query = query.split(",")
        self.user = False
        self.guild = False
        self.title = False
        self.params = {}
        self.scan()
        self.check()


    def scan(self):
        for x in self.query:
            check_user = re.match(regex_user, x)
            if check_user != None:
                self.user = True

            check_guild = re.match(regex_guild, x)
            if check_guild != None:
                self.guild = True

            check_title = re.match(regex_title, x)
            if check_title != None:
                self.title = True

    def getUser(self):
        for i in self.query:
            check_user = re.match(regex_user, i)
            if check_user != None:
                if "@" not in i:
                    x = i.split(":")
                    self.params["user"] = x[1]
                    self.query.remove(i)
                    return
                self.params["user"] = check_user.groups(1)[1]
                self.query.remove(i)

    def getGuild(self):
        for i in self.query:
            check_guild = re.match(regex_guild, i)
            if check_guild != None:
                if "+" not in i:
                    x = i.split(":")
                    self.params["guild"] = x[1]
                    self.query.remove(i)
                    return
                self.params["guild"] = check_guild.groups(1)[1]
                self.query.remove(i)

    def getTitle(self):
        for i in self.query:
            check_title = re.match(regex_title, i)
            if check_title != None:
                i = i.split(":")
                self.params["title"] = i[1]

    def check(self):

        if not self.user and not self.guild and not self.title:
            self.params = {"title": self.query[0]}

        elif self.user and self.guild and self.title:
            self.getUser()
            self.getGuild()
            self.getTitle()

        elif not self.user and not self.guild and self.title:
            self.getTitle()

        elif self.user and not self.guild and self.title:
            self.getUser()
            self.getTitle()

        elif not self.user and self.guild and self.title:
            self.getGuild()
            self.getTitle()

        elif self.user and not self.guild and not self.title:
            self.getUser()

        elif not self.user and self.guild and not self.title:
            self.getGuild()

        elif self.user and not self.guild and not self.title:
            self.getUser()
            self.getGuild()

#query = Search("title:title 23 23 24 25, guild:The_donald, user:@arkitekt")



