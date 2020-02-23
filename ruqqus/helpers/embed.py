import re
from ruqqus.__main__ import app

youtube_regex=re.compile("^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*")
bitchute_regex=re.compile("^.*(bitchute.com\/|embed\/)([^#\&\?]*).*")

def youtube_embed(url):

    try:
        yt_id=re.match(youtube_regex, url).group(2)
    except AttributeError:
        return "error"

    if yt_id and len(yt_id)==11:
        return f"https://youtube.com/embed/{yt_id}"
    else:
        return "error"

def bitchute_embed(url):

    try:
        bc_id=re.match(bitchute_regex, url).group(2)
    except AttributeError:
        return "error"

    if bc_id and len(bc_id)==12:
        return f"https://bitchute.com/embed/{bc_id}"
    else:
        return "error"

ruqqus_regex=re.compile("^.*ruqqus.com/post/(\w+)(/comment/(\w+))?")
def ruqqus_embed(url):

    matches=re.match(ruqqus_regex, url)

    post_id=matches.group(1)
    comment_id=matches.group(2)

    if comment_id:
        return f"https://{app.config['SERVER_NAME']}/embed/comment/{comment_id}"
    else:
        return f"https://{app.config['SERVER_NAME']}/embed/post/{post_id}"

    
