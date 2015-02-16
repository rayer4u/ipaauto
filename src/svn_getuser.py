import os
from os.path import join, expanduser
import subprocess
from sys import platform
import sys
from urlparse import urlparse


url = ""
root = ""
if (platform == "win32"):
    confdir = join(expanduser("~"), "Application Data\\Subversion\\auth\\svn.simple")
else:
    confdir = join(expanduser("~"), ".subversion/auth/svn.simple")

def svnInfo():
    global url,root
    p = subprocess.Popen(['svn', 'info'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if len(err) > 0:
        sys.stderr.write(err)
    else :
        lines = out.splitlines(False)
        root = lines[1].split(': ')[1].strip()
        u = urlparse(lines[4].split(': ')[1].strip())
        url = u.scheme+"://"+u.netloc
#         print("root: "+root)
#         print("url: "+url)
        return True
    return False
        
def userFromFile():
    for root, dirs, files in os.walk(confdir):
        for f in files:
            srcfile = join(root, f)
            r = open(srcfile).read()
            lines = r.splitlines(False)
            if url in r:
                for i,line in enumerate(lines):
                    if line == "username":
#                         print("user: "+lines[i+2])
                        return lines[i+2]
    return ""

def userFromCache():
    return ""

def getUser():
    if svnInfo():
        user = userFromCache()
        if user == "":
            user = userFromFile();
        
        if user != "":
            return(user)

    return ""
            