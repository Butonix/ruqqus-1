from .get import *

from mistletoe.span_token import SpanToken
from mistletoe.html_renderer import HTMLRenderer
import re

# add token/rendering for @username mentions

class UserMention(SpanToken):

    pattern=re.compile("(^|\W)@(\w{3,25})")
    parse_inner=False
    
    def __init__(self, match_obj):
        self.target = (match_obj.group(1), match_obj.group(2))

class BoardMention(SpanToken):

    pattern=re.compile("(^|\s)\+(\w{3,25})")
    parse_inner=False

    def __init__(self, match_obj):

        self.target=(match_obj.group(1), match_obj.group(2))

class CustomRenderer(HTMLRenderer):

    def __init__(self):
        super().__init__(UserMention,
                         BoardMention)

    def render_user_mention(self, token):
        space = token.target[0]
        target = token.target[1]

        user=get_user(target, graceful=True)
        if not user or user.is_banned:
            return f"{space}@{target}"
        
        return f'{space}<a href="{user.permalink}" class="d-inline-block"><img src="/@{user.username}/pic/profile" class="profile-pic-20 mr-1">@{user.username}</a>'

    def render_board_mention(self, token):
        space=token.target[0]
        target=token.target[1]

        board=get_guild(target, graceful=True)

        if not board or board.is_banned:
            return f"{space}+{target}"
        else:
            return f'{space}<a href="{board.permalink}" class="d-inline-block"><img src="/+{board.name}/pic/profile" class="profile-pic-20 align-middle mr-1">+{board.name}</a>'
        
