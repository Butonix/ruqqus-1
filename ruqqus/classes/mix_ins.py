from ruqqus.helpers.base36 import *
import math
import random
import time

from ruqqus.__main__ import cache


class Stndrd:
    @property
    def base36id(self):
        return base36encode(self.id)

    @property
    def created_date(self):
        return time.strftime("%d %B %Y", time.gmtime(self.created_utc))


class Age_times:

    @property
    def age(self):

        now=int(time.time())

        return now-self.created_utc

    @property
    def age_string(self):

        age = self.age

        if age < 60:
            return "just now"
        elif age < 3600:
            minutes = int(age / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif age < 86400:
            hours = int(age / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif age < 2592000:
            days = int(age / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"

        now = time.gmtime()
        ctd = time.gmtime(self.created_utc)
        months = now.tm_mon - ctd.tm_mon + 12 * (now.tm_year - ctd.tm_year)

        if months < 12:
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = int(months / 12)
            return f"{years} year{'s' if years > 1 else ''} ago"

    @property
    def edited_string(self):

        age = int(time.time()) - self.edited_utc

        if age < 60:
            return "just now"
        elif age < 3600:
            minutes = int(age / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif age < 86400:
            hours = int(age / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif age < 2592000:
            days = int(age / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"

        now = time.gmtime()
        ctd = time.gmtime(self.created_utc)
        months = now.tm_mon - ctd.tm_mon + 12 * (now.tm_year - ctd.tm_year)

        if months < 12:
            return f"{months} month{'s' if months > 1 else ''} ago"
        else:
            years = now.tm_year - ctd.tm_year
            return f"{years} year{'s' if years > 1 else ''} ago"

    @property
    def edited_date(self):
        return time.strftime("%d %B %Y", time.gmtime(self.edited_utc))

class Scores:

    @property
    @cache.memoize(timeout=60)
    def score_percent(self):
        try:
            return int((self.ups/(self.ups+self.downs))*100)
        except ZeroDivisionError:
            return 0

    @property
    @cache.memoize(timeout=60)
    def rank_hot(self):
        return (self.ups-self.down)/(((self.age+100000)/6)**(1/3))

    @property
    @cache.memoize(timeout=60)
    def rank_fiery(self):
        return (math.sqrt(self.ups * self.downs))/(((self.age+100000)/6)**(1/3))

    @property
    @cache.memoize(timeout=60)
    def score(self):
        return self.ups-self.downs



class Fuzzing:

    @property
    @cache.memoize(timeout=60)
    def score_fuzzed(self):


        
        real = self.score

        if real <= 10:
            return int(real)

        k=0.01
        
        a = math.floor(real * (1 - k))
        b = math.ceil(real * (1 + k))
        return random.randint(a, b)
