#Ruqqus installation wizard
import pip
import os
from os import environ
import venv
import secrets


print("")
print("")
print('   /\\')
print(' _/__\\_')
print(' ╭───────╮')
print('╭┤  ╹ ╹  ├╮')
print(' ╰─┬───┬─╯')
print("")
print("")
print("Welcome. I am the Ruqqus Installation and Setup Wizard.")
print("I will guide you through the process of setting up your own Ruqqus server.")

#navigate to folder above ruqqus repo
path=os.path.realpath('.')
if path.endswith("scripts"):
    path=os.path.realpath(path+"/..")
if path.endswith("ruqqus"):
    path=os.path.realpath(path+"/..")

files=os.listdir(path)

if "env.sh" in files:
    os.system(f"source {path}/env.sh")

if "venv" not in files:


    print("")
    print("")
    print('   /\\')
    print(' _/__\\_')
    print(' ╭───────╮')
    print('╭┤  ╹ ╹  ├╮')
    print(' ╰─┬───┬─╯')
    print("")
    print("")
    print("First, I will create a virtual Python environment for Ruqqus to run in.")
    print("This pocket universe will contain everything Ruqqus needs.")
    print("This will be created at:")
    print(f"{path}/venv")
    print("")
    input("Press enter to continue.")

    os.system(f"python -m venv {path}/venv")
    os.system(f"source {path}/venv/bin/activate")

    print("We have created and entered the virtual environment.")

else:

    os.system(f"source {path}/venv/bin/activate")
    print("We are now in the python virtual environment.")


print("")
print("")
print('   /\\')
print(' _/__\\_')
print(' ╭───────╮')
print('╭┤  ╹ ╹  ├╮')
print(' ╰─┬───┬─╯')
print("")
print("")
print("Now, I'm going to update the environment with everything Ruqqus needs.")
print("This may take a moment, especially if it's the first time.")
print("")
input("Press enter to continue.")
os.system("pip install -r {path}/ruqqus/requirements.txt")


print("Next, I need some information to cast my setup spells.")
print("This information is required. Optional things will be later.")

envs={}

print("What is the name of your site?")
envs["SITE_NAME"]=input().lower() or environ.get("SITE_NAME")

print("What is the domain that your site will run under?")
envs["SERVER_NAME"]=input() or environ.get("SERVER_NAME") or "localhost:5000"

print("Postgres database url (postgres://username:password@host:port)")
envs["DATABASE_URL"]=input() or environ.get("DATABASE_URL")

print("")
print("")
print('   /\\')
print(' _/__\\_')
print(' ╭───────╮')
print('╭┤  ╹ ╹  ├╮')
print(' ╰─┬───┬─╯')
print("")
print("")
print("Thank you for that.")
print("There's some more information I'd like.")
print("These are optional, but allow for more features and better performance")
print("if you can provide them.")
print("To skip any item, or to leave it at its current setting,just press enter.")

print("Master Secret (If you don't have one already, I'll generate one for you.)")
envs["MASTER_KEY"]=input() or environ.get("MASTER_KEY", secrets.token_urlsafe(1024))

print("Redis url (redis://host)")
envs["REDIS_URL"]=input() or environ.get("REDIS_URL", "")
envs["CACHE_TYPE"]="redis" if envs["REDIS_URL"] else "filesystem"

print("")
print("")
print('   /\\')
print(' _/__\\_')
print(' ╭───────╮')
print('╭┤  ╹ ╹  ├╮')
print(' ╰─┬───┬─╯')
print("")
print("")
print("Next, I'll ask you about some third-party services that I can integrate with.")
print("To skip any item, or to leave it at its current setting,just press enter.")

print("")
print("Are you using CloudFlare? (y/n)")
if input().startswith('y'):

    print("Cloudflare API Key:")
    envs["CLOUDFLARE_KEY"]=input() or environ.get("CLOUDFLARE_KEY","")

    print("Cloudflare Zone:")
    envs["CLOUDFLARE_ZONE"]=input() or environ.get("CLOUDFLARE_ZONE","")

print("Are you using AWS S3 to host images? (y/n)")
if input().startswith('y'):

    print("S3 Bucket Name")
    print(f"This should be a subdomain of your main site domain, for example, i.{envs['SERVER_NAME']}")
    envs["S3_BUCKET_NAME"]=input() or environ.get("S3_BUCKET_NAME","")

    print("AWS Access Key ID:")
    envs["AWS_ACCESS_KEY_ID"]=input() or environ.get("AWS_ACCESS_KEY_ID","")

    print("AWS Secret Access Key:")
    envs["AWS_SECRET_ACCESS_KEY"]=input() or environ.get("AWS_SECRET_ACCESS_KEY","")

print("Are you using HCaptcha to block bot signups?")
if input().startswith('y'):
    print("HCaptcha Site Key")
    envs["HCAPTCHA_SITEKEY"]=input() or environ.get("HCAPTCHA_SITEKEY")

    print("HCaptcha Secret")
    envs["HCAPTCHA_SECRET"]=input() or environ.get("HCAPTCHA_SECRET")

keys=[x for x in envs.keys()].sorted()

with open(f"{path}/env.sh", "w+") as f:
    f.write("\n".join([f"export {x}={envs[x]}" for x in keys]))

start_script="""
killall gunicorn
cd ~/ruqqus
git pull
source startup.sh
"""
with open(f"{path}/go.sh", "w+") as f:
    f.write(start_script)


print("")
print("")
print('   /\\')
print(' _/__\\_')
print(' ╭───────╮')
print('╭┤  ╹ ╹  ├╮')
print(' ╰─┬───┬─╯')
print("")
print("")
print("Ruqqus is set up! To start Ruqqus navigate to the folder above the repository and run `source go.sh`")