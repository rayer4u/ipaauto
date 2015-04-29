# ios的应用自动打包、上传工具。
和服务器端[ipapub][1]自动签名发布工具结合，以实现多项目的多证书的打包、签名、发布的全自动化。
ipaauto主要实现，自动替换、配置，证书变更，以发布不同渠道包。并把打包和签名发布分离开，开发不用在关心各种证书描述文件的麻烦，签名发布由服务器统一管理
* 通过读取运行的当前目录auto.cfg配置文件。进行项目的拷贝、覆盖、配置文件的自动替换
* 命名规则读取auto.cfg里的general段里的一些字段，按照一定的固定规则自动生成。
* 项目依赖requests库实现上传功能，请用pip安装
* 发布完成返回的url直接打开可以实现ipa包的安装
* 项目依赖svn命令行工具获取用户名上传，如无需要修改ipa_auto的 user = getUser()部分

## 运行参数
* **-publish** 这样会生成正式发布包。依赖**publish段**的*Url字段
* **-continue** 会跳过前面的拷贝覆盖过程，直接进入xcodebuild
* **_xxx** 会使用当前目录的auto_xxx.cfg命名的配置文件进行运行打包。xxx是任意有效的文件名称字符串。如无此项默认使用auto.cfg

## auto.cfg详解
1. **general段**是通用设置，用于自动相关或者多处替换，比如id在这里定义了，其他段里使用{{ id }}就能引用。其中id、name、versionCode、versionName、signUrl是必须项。其他根据项目需求定义
2. **build段**是xcodebuild命令的参数选择，比如configuration=Release/Debug的选择。宏定义使用*{%宏%}*的形式定义，宏定义会自动大写。有几个宏说明下
   * CODE_SIGN_IDENTITY用于指定签名证书。建议和CODE_SIGNING_REQUIRED一起使用，在本地不签名
   * PROVISIONING_PROFILE用户指定项目的描述文件。不指定自动使用的项目里的描述文件。
   * GCC_PRECOMPILE_PREFIX_HEADER设为NO表明不使用预编译头文件。用于解决编译问题。如果编译没有问题不用设
    
3. **sign段**是签名的证书和描述文件的选择，具体依赖[ipapub][1]项目里的定义
4. **publish段**用作测试和正式发布的自动打包plist参数定义，*url字段用于正式发布
   * iconSmallPath 是发布plist的*display-image*字段所用到的图标的本地路径，**必填字段**
   * iconBigPath 是发布plist的*full-size-image*字段所用到的图标的本地路径，**必填字段**
   * ipaUrl，iconSmallUrl，iconBigUrl是正式发布时所用的plist相应字段，plistUrl用于正式发布包里的plist文件名

5. **其他字段**是可以支持的配置文件的替换。目前支持**plist字段**和**h头文件宏定义**的替换。后续可以支持普通cfg以及使用xpath支持xml的替换

## 编译问题
* 如果编译时出现头文件预编译头文件过期的的问题，目前在xcode 6.1上有可能遇到。请在build段使用宏`{%GCC_PRECOMPILE_PREFIX_HEADER%}=NO`禁用预编译头文件
* 如果出现证书问题，请`{%CODE_SIGN_IDENTITY%}= `和`{%CODE_SIGNING_REQUIRED%}=NO`表明在编译时不使用证书，这样完全在开发测不依赖证书描述文件，以避免多证书时的混乱




[1]: <https://github.com/rayer4u/ipapub>  "ipapub项目"

