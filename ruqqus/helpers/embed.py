import re

youtube_regex=re.compile("^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*")

def youtube_embed(url):

    try:
        yt_id=re.match(youtube_regex, url).group(2)
    except AttributeError:
        return "error"

    if yt_id and len(yt_id)==11:
        return f"https://youtube.com/embed/{yt_id}"
    else:
        return "error"
