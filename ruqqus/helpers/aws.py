import boto3
import requests
from os import environ, remove
import piexif
import time
from urllib.parse import urlparse
from PIL import Image

BUCKET = "i.ruqqus.com"
CF_KEY = environ.get("CLOUDFLARE_KEY").lstrip().rstrip()
CF_ZONE = environ.get("CLOUDFLARE_ZONE")

# setup AWS connection
S3 = boto3.client("s3",
                  aws_access_key_id=environ.get(
                      "AWS_ACCESS_KEY_ID").lstrip().rstrip(),
                  aws_secret_access_key=environ.get(
                      "AWS_SECRET_ACCESS_KEY").lstrip().rstrip()
                  )


def upload_from_url(name, url):

    print('upload from url')

    x = requests.get(url)

    print('got content')

    tempname = name.replace("/", "_")

    with open(tempname, "wb") as file:
        for chunk in r.iter_content(1024):
            f.write(chunk)

    if tempname.split('.')[-1] in ['jpg', 'jpeg']:
        piexif.remove(tempname)

    S3.upload_file(tempname,
                   Bucket=BUCKET,
                   Key=name,
                   ExtraArgs={'ACL': 'public-read',
                              "ContentType": "image/png",
                              "StorageClass": "INTELLIGENT_TIERING"
                              }
                   )

    remove(tempname)


def crop_and_resize(img, resize):

    i = img

    # get constraining dimension
    org_ratio = i.width / i.height
    new_ratio = resize[0] / resize[1]

    if new_ratio > org_ratio:
        crop_height = int(i.width / new_ratio)
        box = (0, (i.height // 2) - (crop_height // 2),
               i.width, (i.height // 2) + (crop_height // 2))
    else:
        crop_width = int(new_ratio * i.height)
        box = ((i.width // 2) - (crop_width // 2), 0,
               (i.width // 2) + (crop_width // 2), i.height)

    return i.resize(resize, box=box)


def upload_file(name, file, resize=None):

    # temp save for exif stripping
    tempname = name.replace("/", "_")

    file.save(tempname)

    if tempname.split('.')[-1] in ['jpg', 'jpeg']:
        piexif.remove(tempname)

    if resize:
        i = Image.open(tempname)
        i = crop_and_resize(i, resize)
        i.save(tempname)

    S3.upload_file(tempname,
                   Bucket=BUCKET,
                   Key=name,
                   ExtraArgs={'ACL': 'public-read',
                              "ContentType": "image/png"
                              }
                   )

    remove(tempname)


def upload_from_file(name, filename, resize=None):

    tempname = name.replace("/", "_")

    if filename.split('.')[-1] in ['jpg', 'jpeg']:
        piexif.remove(tempname)

    if resize:
        i = Image.open(tempname)
        i = crop_and_resize(i, resize)
        i.save(tempname)

    S3.upload_file(tempname,
                   Bucket=BUCKET,
                   Key=name,
                   ExtraArgs={'ACL': 'public-read',
                              "ContentType": "image/png"
                              }
                   )

    remove(filename)


def delete_file(name):

    S3.delete_object(Bucket=BUCKET,
                     Key=name)

    # After deleting a file from S3, dump CloudFlare cache

    headers = {"Authorization": f"Bearer {CF_KEY}",
               "Content-Type": "application/json"}
    data = {'files': [f"https://{BUCKET}/{name}"]}
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/purge_cache"

    x = requests.post(url, headers=headers, json=data)


def check_csam(post):

    # Relies on Cloudflare's photodna implementation
    # 451 returned by CF = positive match

    # ignore non-link posts
    if not post.url:
        return

    parsed_url = urlparse(post.url)

    if parsed_url.netloc != BUCKET:
        return

    headers = {"User-Agent": "Ruqqus webserver"}
    for i in range(10):
        x = requests.get(post.url, headers=headers)

        if x.status_code in [200, 451]:
            break
        else:
            time.sleep(20)

    if x.status_code != 451:
        return

    # ban user and alts
    post.author.is_banned = 1
    g.db.add(v)
    for alt in post.author.alts:
        alt.is_banned = 1
        g.db.add(alt)

    # remove content
    post.is_banned = True
    g.db.add(post)

    # nuke aws
    delete_file(parsed_url.path.lstrip('/'))


def check_csam_url(url, v, delete_content_function):

    parsed_url = urlparse(url)

    if parsed_url.netloc != BUCKET:
        return

    headers = {"User-Agent": "Ruqqus webserver"}
    for i in range(10):
        x = requests.get(url, headers=headers)

        if x.status_code in [200, 451]:
            break
        else:
            time.sleep(20)

    if x.status_code != 451:
        return

    v.is_banned = 1
    g.db.add(v)
    for alt in v.alts:
        alt.is_banned = 1
        g.db.add(alt)

    delete_content_function()
