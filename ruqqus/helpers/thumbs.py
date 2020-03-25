import requests
from os import environ
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from .get import *
from ruqqus.__main__ import db, app

def thumbnail_thread(pid):

    post=get_post(pid)

    #step 1: see if post is image

    print("thumbnail thread")

    domain_obj=post.domain_obj

    if domain_obj and domain_obj.show_thumbnail:
        print("image post")
        x=requests.head(post.url)

        if x.headers.get("Content-Type","/").split("/")[0]=="image":
            post.is_image=True
            db.add(post)
            db.commit()

            return

##    url=f"https://api.apiflash.com/v1/urltoimage"
##    params={'access_key':environ.get("APIFLASH_KEY"),
##            'format':'png',
##            'height':720,
##            'width':1280,
##            'response_type':'image',
##            'thumbnail_width':600,
##            'url': post.embed_url if post.embed_url else post.url,
##            'css':"iframe {display:none;}"
##            }

    headers={"User-Agent":app.config['UserAgent']}
    x=requests.get(post.url, headers=headers)
    
    if x.status_code != 200 or not x.headers["Content-Type"].startswith("text/html"):
        print(f'not html post, status {x.status_code}')
        return

    soup=BeautifulSoup(x.content, 'html.parser')
    img=soup.find('meta', attrs={"name": "thumbnail"})
    if img:
        src=img['content']
    else:
    
        img=soup.find('img', src=True)
        if img:
            src=img['src']
        else:
            print('no image in doc')
            return

    #convert src into full url
    if src.startswith("https://"):
        pass
    elif src.startswith("http://"):
        src=f"https://{src.split('http://')}"
    elif src.startswith('//'):
        src=f"https:{src}"
    elif src.startswith('/'):
        parsed_url=urlparse(post.url)
        src=f"https://{parsed_url.netloc}/{src.lstrip('/')}"
    else:
        src=f"{post.url}{'/' if not post.url.endswith('/') else ''}{src}"

    
    x=requests.get(src, headers=headers)
    print("have first image")

    if x.status_code!=200:
        print('no image')
        return

    name=f"posts/{post.base36id}/thumb.png"
    tempname=name.replace("/","_")

    with open(tempname, "wb") as file:
        for chunk in x.iter_content(1024):
            file.write(chunk)

    print("thumb saved")

    aws.upload_from_file(name, tempname)
    post.has_thumb=True
    db.add(post)
    db.commit()

    print("thumb all success")
