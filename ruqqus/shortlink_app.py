from flask import *

app=Flask(__name__)

app.config["SERVER_NAME"]="www.ruqq.us"

@app.route("/<pid>", methods=["GET"])
def pid(pid):
    return redirect(f"https://www.ruqqus.com/post/{pid}")

@app.route("/<pid>/<cid>", methods=["GET"])
def pid_cid(pid, cid):
    return redirect(f"https://www.ruqqus.com/post/{pid}/comment/{cid}")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=8000)
