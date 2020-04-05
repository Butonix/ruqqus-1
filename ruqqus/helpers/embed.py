import re
from urllib.parse import *
from ruqqus.__main__ import app

youtube_regex=re.compile("^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*")

def youtube_embed(url):

    try:
        yt_id=re.match(youtube_regex, url).group(2)
    except AttributeError:
        return "error"

    

    if not yt_id or  len(yt_id)!=11:
        return "error"

    x=urlparse(url)
    params=parse_qs(x.query)
    t=params.get('t',params.get('start', [0]))[0]
    if t:
        return f"https://youtube.com/embed/{yt_id}?start={t}"
    else:
        return f"https://youtube.com/embed/{yt_id}"



ruqqus_regex=re.compile("^.*ruqqus.com/post/(\w+)(/comment/(\w+))?")
def ruqqus_embed(url):

    matches=re.match(ruqqus_regex, url)

    post_id=matches.group(1)
    comment_id=matches.group(3)

    if comment_id:
        return f"https://{app.config['SERVER_NAME']}/embed/comment/{comment_id}"
    else:
        return f"https://{app.config['SERVER_NAME']}/embed/post/{post_id}"

    
