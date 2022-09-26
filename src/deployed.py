import os

def start_deployed():
    try:
        os.chdir("deploy")
    except:
        os.mkdir("deploy")
        os.chdir("deploy")
    with open("__init__.py", "r") as f:
        exec(f.read())
