import boto3
import requests
from os import environ, remove
import piexif
from PIL import Image

BUCKET="i.ruqqus.com"

#setup AWS connection
S3=boto3.client("s3",
                aws_access_key_id=environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=environ.get("AWS_SECRET_ACCESS_KEY")
                )

def upload_from_url(name, url):

    print('upload from url')
    
    x=requests.get(url)

    print('got content')

    tempname=name.replace("/","_")

    with open(tempname, "wb") as file:
        for chunk in r.iter_content(1024):
            f.write(chunk)
            
    if tempname.split('.')[-1] in ['jpg','jpeg']:
        piexif.remove(tempname)
    
    S3.upload_file(tempname,
                      Bucket=BUCKET,
                      Key=name,
                      ExtraArgs={'ACL':'public-read',
                                 "ContentType":"image/png"
                      }
                     )

    remove(tempname)
    

def upload_file(name, file):

    #temp save for exif stripping
    tempname=name.replace("/","_")

    file.save(tempname)
    
    if tempname.split('.')[-1] in ['jpg','jpeg']:
        piexif.remove(tempname)
    
    S3.upload_file(tempname,
                      Bucket=BUCKET,
                      Key=name,
                      ExtraArgs={'ACL':'public-read',
                                 "ContentType":"image/png"
                      }
                     )

    remove(tempname)

def upload_from_file(name, filename):

    tempname=name.replace("/","_")

    if filename.split('.')[-1] in ['jpg','jpeg']:
        piexif.remove(tempname)
    
    S3.upload_file(tempname,
                      Bucket=BUCKET,
                      Key=name,
                      ExtraArgs={'ACL':'public-read',
                                 "ContentType":"image/png"
                      }
                     )

    remove(filename)

def delete_file(name):

    S3.delete_object(Bucket=BUCKET,
                     Key=name)

    
