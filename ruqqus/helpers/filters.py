import yaml

config=yaml.load(open("banned.txt", "r+"))

def filter_post(post):

    if any([post.domain.endswith(x) for x in config["nosubmit"]]):
        return render_template("submit.html", error=f"{post.domain} isn't allowed.")

