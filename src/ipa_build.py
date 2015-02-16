#coding:utf-8
from __future__ import print_function

import os
import re
import subprocess
import sys


def ipa_build(builds):

    rule = re.compile(r"^Validate (.*)\s*")
    cmd = 'xcodebuild build -sdk iphoneos'+\
        ''.join(' -'+key+' '+str(value) for key,value in builds.items()) #CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO
    print(cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=os.environ, shell=True)
      
    path = ''
    while True:
        line = p.stdout.readline()
        if not line:
            break
        print(line)
      
        mt = rule.match(line)
        if mt:
            path = mt.group(1)
      
    err = p.wait()
    if err != 0:
        print("app build failed", file=sys.stderr)
        return ""
#     path = 'Mlplayer.app' #'build/Release-iphoneos/MLPlayer.app'
    pathnew = os.path.basename(path)+'.tgz'
    cmdtar = 'tar -czf '+pathnew+' -C '+('.' if os.path.dirname(path) == '' else os.path.dirname(path))+' '+os.path.basename(path)
    print(cmdtar)
    print()
    p = subprocess.Popen(cmdtar, stdout=subprocess.PIPE, env=os.environ, shell=True)
    err = p.wait()
    if err != 0:
        print("app tar %s failed"%path, file=sys.stderr)
        return ""    
    
    return pathnew
