import requests
from os import environ, remove
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from PIL import Image as PILimage

from .get import *
from ruqqus.__main__ import db, app

def thumbnail_thread(pid):

    post=get_post(pid)

    #step 1: see if post is image

    print("thumbnail thread")

    domain_obj=post.domain_obj

    if domain_obj and domain_obj.show_thumbnail:
        #print("image post")
        x=requests.head(post.url)

        if x.headers.get("Content-Type","/").split("/")[0]=="image":
            post.is_image=True
            db.add(post)
            db.commit()

            return

    headers={"User-Agent":app.config['UserAgent']}
    x=requests.get(post.url, headers=headers)
    
    if x.status_code != 200 or not x.headers["Content-Type"].startswith(("text/html", "image/")):
        #print(f'not html post, status {x.status_code}')
        return
    
    if x.headers["Content-Type"].startswith("image/"):
        pass
        #submitted url is image
        
    elif x.headers["Content-Type"].startswith("text/html"):

        soup=BeautifulSoup(x.content, 'html.parser')
        img=soup.find('meta', attrs={"name": "ruqqus:thumbnail", "content":True})
        if not img:
            img=soup.find('meta', attrs={"name":"twitter:image", "content":True})
        if not img:
            img=soup.find('meta', attrs={"name": "thumbnail", "content":True})
        if img:
            src=img['content']
        else:

            imgs=soup.find_all('img', src=True)
            if imgs:
                #print("using first <img>")
                pass
            else:
                #print('no image in doc')
                return

            #Loop through all images in document until we find one that works (and isn't svg)
            for img in imgs:
                
                src=img["src"]
                
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
    

                #load asset
                x=requests.get(src, headers=headers)


                if x.status_code!=200:
                    #print('no image')
                    continue
                    
                type=x.headers.get("Content-Type","")

                if not type.startswith("image/"):
                    continue
                
                if type.startswith("image/svg"):
                    continue
                
                break

    name=f"posts/{post.base36id}/thumb.png"
    tempname=name.replace("/","_")

    with open(tempname, "wb") as file:
        for chunk in x.iter_content(1024):
            file.write(chunk)

    i=PILimage.open(tempname)
    i=i.resize((98,68))
    i.save(tempname)

    aws.upload_from_file(name, tempname)
    post.has_thumb=True
    db.add(post)
    db.commit()
    
    #remove(tempname)
