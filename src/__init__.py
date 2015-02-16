# -*- coding: utf-8 -*-
"""
打包、签名、上传脚本
----------------------------
打包基于xcodebuild，
python获取返回的打包好的文件名，以及svn的用户名信息，上传到服务器自动签名，并返回相应访问url

打包需要以下前置条件
ant编译打包成功
正确的获取svn用户名，意味者需要基于svn系统
"""

__title__ = 'apkauto'
__version__ = '1.0.1'
__build__ = 0x010001
__author__ = 'roybi'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2015'
