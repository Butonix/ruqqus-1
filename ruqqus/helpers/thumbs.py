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

    #print("thumbnail thread")

    domain_obj=post.domain_obj

    if domain_obj and domain_obj.show_thumbnail:

        x=requests.head(post.url)

        if x.headers.get("Content-Type","/").split("/")[0]=="image":
            #print("image post, using submitted url")
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

        metas = ["ruqqus:thumbnail",
                 "twitter:image",
                 "thumbnail"
                 ]

        for meta in metas:
            
            img=soup.find('meta', attrs={"name": meta, "content":True})
            if not img:
                continue
            try:
                x=requests.get(img['content'], headers=headers)
            except:
                continue
            break
            
        if not img or not x or x.status_code != 200:

            imgs=soup.find_all('img', src=True)
            if imgs:
                #print("using <img> elements")
                pass
            else:
                #print('no image in doc')
                return

            #Loop through all images in document until we find one that works (and isn't svg)
            for img in imgs:
                
                src=img["src"]
                
                #print("raw src: "+src)
                
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
                    
                #print("full src: "+src)
    

                #load asset
                x=requests.get(src, headers=headers)


                if x.status_code!=200:
                    #print('not 200, next')
                    continue
                    
                type=x.headers.get("Content-Type","")

                if not type.startswith("image/"):
                    #print("not an image, next")
                    continue
                
                if type.startswith("image/svg"):
                    #print("svg image, next")
                    continue
                
                break

    name=f"posts/{post.base36id}/thumb.png"
    tempname=name.replace("/","_")

    with open(tempname, "wb") as file:
        for chunk in x.iter_content(1024):
            file.write(chunk)


    aws.upload_from_file(name, tempname, resize=(375,227))
    post.has_thumb=True
    db.add(post)
    db.commit()
    
    #remove(tempname)
