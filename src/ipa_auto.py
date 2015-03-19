# -*- coding: utf-8 -*-
"""
大小写 不区分
plist 要求一行一记录
      只支持key的value修改
h     define不支持函数，只支持字符串，数字的替换
      一般只有一个定义，多个同名定义都会被替换
mlplayer.cfg  一种xml解析，
"""

from __future__ import print_function

import sys
import ConfigParser
import shutil
import os
import tempfile
import re
import requests
import json
import xml.etree.ElementTree as ET 
from time import gmtime, strftime

from ipa_build import ipa_build
from svn_getuser import getUser

cfg = 'auto.cfg'
def ipa_auto(label, pub, url, con):
    cf = ConfigParser.SafeConfigParser()    
    cf.read(cfg)  
    
    sections = cf.sections();
    
    #general setting
    gens={}
    if 'general' in sections:
        gens = dict(cf.items('general'))
        sections.remove('general')
        print(gens)
        print()
    
    #build params
    builds={}
    if 'build' in sections:
        builds = dict(cf.items('build'))
        sections.remove('build')
    
    #post params
    signs={}
    if 'sign' in sections:
        signs = dict(cf.items('sign'))
        sections.remove('sign')
    
    pubs={}
    #publish
    if 'publish' in sections:
        pubs = dict(cf.items('publish'))
        sections.remove('publish') 
    
    #copy dirs
    dst_dir = '.'
    build_dir = '.'
    if 'copy_dirs' in sections:
        base_dir = cf.get('copy_dirs', 'BASE_DIR')
        replace_dir = cf.get('copy_dirs', 'REPLACE_DIR')
        tmp_dir = cf.get('copy_dirs', 'TMP_DIR')
        
        if base_dir == '':
            print("BASE_DIR in %s must not null"%(cfg), file=sys.stderr)
            return
        if tmp_dir != '':
            if not con and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
            print('dir move %s to %s'%(base_dir, tmp_dir))
            print()
            if not con:
                shutil.copytree(base_dir, tmp_dir, ignore=None)
            dst_dir = tmp_dir
        else:
            dst_dir=base_dir
        if cf.has_option('copy_dirs', 'BUILD_DIR'):
            build_dir = cf.get('copy_dirs', 'BUILD_DIR')
        else:
            build_dir = dst_dir
        if replace_dir != '':
            print('dir replace %s to %s'%(replace_dir, dst_dir))
            print()
            if not con:
                replacetree(replace_dir, dst_dir)
        sections.remove('copy_dirs')
    
    if not con:
        for section in sections:
            options = dict(cf.items(section))
            _,ext = os.path.splitext(section)
            do_replace = do_unsupport
            if ext != None:
                if ext == '.plist':
                    #plist文件的替换
                    do_replace = do_plist
                elif ext == '.h':
                    #h头文件define的替换
                    do_replace = do_h_define
            if os.path.basename(section) == 'mlplayer.cfg':
                do_replace = do_mlplayer_cfg
            print(section)
            repl(options, gens)
            do_replace(os.path.join(dst_dir, section), options)
            print()

    #获取user
    user = getUser()
    if user == "":
        print("error svn get user", file=sys.stderr)
        return  
     
    #jump to dst_dir
    os.chdir(build_dir)
     
    #build 
    fn = ipa_build(builds, con)
    if fn == "":
        print("error build", file=sys.stderr)
        return
       
    #post, path id is used for server
    path = gens['id']+"/"+gens['id']+'-'+gens['versionname']+'-'+builds['configuration']+'-'+strftime("%y%m%d%H%M%S", gmtime())
    files={}
    files['id'] = ('', gens['id'])
    files['file'] = (os.path.basename(fn), open(fn, 'rb'), 'application/x-gtar')
    files['path'] = ('', path)
    files['user'] = ('', user)
    if pub:
        files['ipaurl'] = ('', pubs['ipaurl'])
        files['plisturl'] = ('', pubs['plisturl'])
        files['iconsmallurl'] = ('', pubs['iconsmallurl'])
        files['iconbigurl'] = ('', pubs['iconbigurl'])
    if 'iconsmallpath' in pubs:
        files['icons'] = (os.path.basename(pubs['iconsmallpath']), open(pubs['iconsmallpath'], 'rb'), 'image/png')
    if 'iconbigpath' in pubs:
        files['iconb'] = (os.path.basename(pubs['iconbigpath']), open(pubs['iconbigpath'], 'rb'), 'image/png')
    #for use in plist
    if 'idfix' not in gens:
        gens['idfix'] = gens['id']+'ios8fix'
    plist = rule_repl.sub(lambda mt:gens[mt.group(2).lower()] if mt.group(2).lower() in gens else mt.group(1)+mt.group(2)+mt.group(3), pub_plist)
    files['plist'] = ('',plist)
    if label != "":
        files['label'] = ('',label)
    for key,value in signs.items():
        files[key] = ('', value)
        
    if url == "":
        url = gens['signurl']
    try:
        print("uploading to %s"%url)
        print(files)
        print("")
        rep = requests.post(url, files=files, verify=False)
        if rep.status_code == 200:
            ret = json.loads(rep.content)
            if 'url' in ret:
                print("success upload and sign. url is:")
                print(ret['url'])
                return
            else:
                print(rep.content, file=sys.stderr)
        else:
            print(rep.content, file=sys.stderr)
    except Exception, e:
        print(e, file=sys.stderr)

    

def do_unsupport(pn, options):
    print(pn, options, file=sys.stderr)
    print("unsupport replace", file=sys.stderr)
    return False
    
rule_plistkey = re.compile(r"^\s*<key>(.*)</key>\s*")
rule_plistvalue = re.compile(r"^(\s*<([A-Za-z0-9]+)>)(.*)(</\2>\s*)")
rule_hdefine = re.compile(r"^(\s*#define\s+)([A-Za-z0-9\_]+)(\s+)(0?[A-Fa-f0-9]+|\@?(\").*?[^\\]?\5)(\s*.*\s*|\/{2}.*\s*)")
rule_repl = re.compile(r"(\{\{)(.*)(\}\})")

def repl(options, gens):
    for key,value in options.items():
        valuenew = rule_repl.sub(lambda mt:gens[mt.group(2).lower()], value)
        if valuenew != value:
            options[key] = valuenew
    
def do_plist(pn, options):
    keys = options.keys()

    ret = False
    fr = open(pn, 'rb')
    fw = tempfile.NamedTemporaryFile(dir=os.path.dirname(pn), delete=False)
    try:
        cur = ''
        while True:
            line = fr.readline()
            if line is None or line == '':
                break;
            if cur == '':
                mt = rule_plistkey.match(line)
                if mt is not None:
                    if mt.group(1).lower() in keys:
                        cur = mt.group(1).lower()
                        print(line[:-1])
                
            else:
                mt = rule_plistvalue.match(line)
                if mt is not None:
                    line = mt.group(1)+options[cur]+mt.group(4)
                    print("value "+mt.group(3)+" to "+options[cur])
                else:
                    print("err match %s"%line)
                cur = ''
            fw.write(line)
        ret = True
        
        fw.flush()
        os.fsync(fw.fileno())
        fw.close()
    except Exception as err:
        print("failed %s"%err, file=sys.stderr)
    
    if ret:
        os.remove(pn)
        os.rename(fw.name, pn)
    else:
        os.remove(fw.name)   

    fr.close()
    return ret
    
def do_h_define(pn, options):
    keys = options.keys()
    
    ret = False
    fr = open(pn, 'rb')
    fw = tempfile.NamedTemporaryFile(dir=os.path.dirname(pn), delete=False)
    try:
        while True:
            line = fr.readline()
            if line is None or line == '':
                break;
            mt = rule_hdefine.match(line)
            if mt is not None:
                if mt.group(2).lower() in keys:
                    linen = mt.group(1)+mt.group(2)+mt.group(3)+options[mt.group(2).lower()]+mt.group(6)
                    print(mt.group(2)+" value "+mt.group(4)+" to "+options[mt.group(2).lower()])
                    line = linen
            fw.write(line)

        ret = True
        
        fw.flush()
        os.fsync(fw.fileno())
        fw.close()
    except Exception as err:
        print("failed %s"%err, file=sys.stderr)
    
    if ret:
        os.remove(pn)
        os.rename(fw.name, pn)
    else:
        os.remove(fw.name)   

    fr.close()
    return ret

def do_mlplayer_cfg(pn, options):
    ret = False

    try:
        tree = ET.parse(pn)
        for option_key,option_value in options.items():
            if '|' in option_key:
                elems = tree.findall(option_key.split('|')[0])
            else:
                elems = tree.findall(option_key)
            if elems is not None:
                key = ''
                value = ''
                if '|' in option_key:
                    key = option_key.split('|')[1]
                    value = option_value.decode('utf-8')
                else:
                    if '=' in option_value:
                        key = option_value.split('=')[0]
                        value = option_value.split('=')[1].decode('utf-8')
                    else:
                        value = option_value.decode('utf-8')

                for ele in elems:
                    if key == '':
                        print(ele.tag+" text "+(ele.text if ele.text is not None else "")+" to "+value)
                        ele.text = value
                    else:
                        print(ele.tag+" "+key+" "+ele.get(key)+" to "+value)
                        ele.set(key,value)
        tree.write(pn, encoding='utf-8')
        ret = True

    except Exception as err:
        print("failed %s"%err, file=sys.stderr)

    return ret

#almost same as shutil.copytree, execpt dst can exist
def replacetree(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                replacetree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                shutil.copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error, err:
            errors.extend(err.args[0])
        except EnvironmentError, why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError, why:
        if shutil.WindowsError is not None and isinstance(why, shutil.WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise shutil.Error, errors    
    
pub_plist="""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
   <key>items</key>
   <array>
       <dict>
           <key>assets</key>
           <array>
               <dict>
                   <key>kind</key>
                   <string>software-package</string>
                   <key>url</key>
                   <string>{{ipaUrl}}</string>
                </dict>
                <dict>
                   <key>kind</key>
                   <string>display-image</string>
                   <key>needs-shine</key>
                   <true/>
                   <key>url</key>
                   <string>{{iconSmallUrl}}</string>
                </dict>
            <dict>
                   <key>kind</key>
                   <string>full-size-image</string>
                   <key>needs-shine</key>
                   <true/>
                   <key>url</key>
                   <string>{{iconBigUrl}}</string>
            </dict>
            </array><key>metadata</key>
               <dict>
               <key>bundle-identifier</key>
               <string>{{idfix}}</string>
               <key>bundle-version</key>
               <string>{{versionName}}</string>
               <key>kind</key>
               <string>software</string>
               <key>subtitle</key>
               <string>{{name}}</string>
               <key>title</key>
               <string>{{name}}</string>
            </dict>
       </dict>
    </array>
</dict>
</plist>
"""