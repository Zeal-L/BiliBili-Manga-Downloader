# 🎉 哔哩哔哩漫画下载器 💖

![GitHub Pipenv locked Python version](https://img.shields.io/github/pipenv/locked/python-version/Zeal-L/BiliBili-Manga-Downloader)
![GitHub top language](https://img.shields.io/github/languages/top/Zeal-L/BiliBili-Manga-Downloader)
![GitHub Lines of code](https://img.shields.io/tokei/lines/github/Zeal-L/BiliBili-Manga-Downloader)
![GitHub repo size](https://img.shields.io/github/repo-size/Zeal-L/BiliBili-Manga-Downloader)
![GitHub - License](https://img.shields.io/github/license/Zeal-L/BiliBili-Manga-Downloader)

![platform](https://img.shields.io/badge/platform-windows10-blue)
![GitHub commit activity](https://img.shields.io/github/commit-activity/y/Zeal-L/BiliBili-Manga-Downloader)
![GitHub last commit](https://img.shields.io/github/last-commit/Zeal-L/BiliBili-Manga-Downloader)
![GitHub all releases - Download](https://img.shields.io/github/downloads/Zeal-L/BiliBili-Manga-Downloader/total)

[![CodeQL](https://github.com/Zeal-L/BiliBili-Manga-Downloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/Zeal-L/BiliBili-Manga-Downloader/actions/workflows/codeql.yml)
[![Codiga](https://api.codiga.io/project/35529/status/svg)](https://app.codiga.io/hub/project/35529/BiliBili-Manga-Downloader)
[![Codiga](https://api.codiga.io/project/35529/score/svg)](https://app.codiga.io/hub/project/35529/BiliBili-Manga-Downloader)

## 💬 简介
**由于作者某天实在是受不了B漫网页版的观看体验 ~~(时而混入漫画中的广告，无法便捷快速的放大图片，进度栏作死一样的反复横跳挡视线等等...)~~，再加上作者的仓鼠属性 😛**

**因此 将将将~ 🎉 一个好用的哔哩哔哩漫画下载器就此诞生！**
<div align=center>
<img src="https://user-images.githubusercontent.com/72005386/222969436-a31d4d16-2d24-40ba-bb0b-06c883ba7406.png" width=90%>
<img src="https://user-images.githubusercontent.com/72005386/222970947-25bad523-5fac-4a95-972e-2186b774f535.jpg" width=90%>
</div>

## :sparkles: 主要功能 / 特性
- **已打包成单个可执行文件，双击即用！**
- **易操作的图形界面！~~(不用再费劲的部署环境跑命令行)~~**
- **无需漫画ID，可直接关键词搜索漫画！并附带搜索词高亮！**
- **丰富的漫画详情信息，以及双击漫画封面即可跳转B漫链接！**
- **可配置的多线程下载，速度拉满！**
- **实现了应对网络波动等情况的异常重试，以及应用了指数级退让来避免在短时间大量重试被拉黑名单**
- **本地漫画管理功能，一键检查更新！**
- **通过正则匹配过滤重复的章节名称内容，以及过滤非法字符！**
- **提供多种可选的保存格式：**
  - PDF
  - 7z压缩包
  - 文件夹-图片形式
- **贴心的在保存文件属性中附加了漫画名，章节名以及作者信息，以免单章传播时不知道来源**
- **可视化的多任务下载进度条以及下载速度和剩余时间预计信息！**
- **漫画保存地址和用户Cookie等用户设置的本地缓存，不需要每次重启软件就重新输入！**
- **丰富的错误信息日志，可按照日期滚动储存，不会浪费内存**
- **一键清空用户数据，妈妈再也不用担心我删不干净软件了！~~(bushi)~~**

## 📝 使用指南
- **本软件只能下载免费章节和用户已解锁的章节 ~~(很遗憾并没有什么黑科技钞能力,不过呢有需要的可以参考联系方式)~~**
- **兼容性：目前只在64位的Winodw 10上测试通过，不过其他>=windows 10的版本应该都能运行，发现问题的欢迎提Issues**
- **首先获得你的Cookie**
  1. 以谷歌浏览器为例，打开B漫首页并且登入
  2. 点击顶部地址栏左侧的🔒图标
  3. 点击Cookie选项
  4. 在弹出的界面中依次展开"bilibili.com" -> "Cookie"
  5. 找到"SESSDATA"值，复制"内容"粘贴到程序设置选项中的"我的Cookie"，回车确认
  6. 如果提示"Cookie有效！"那么就成功了！
  7. 否则请再次确认上述步骤，检查是否正确复制内容不含空格，还有疑问的话欢迎联系作者或提Issues
- **搜索 / 选择章节 / 下载 的功能介绍我想已经不言而喻了，这就是图形化界面的好处！**
- **值得注意的是：本软件还未实现断点续传和下载任务缓存的功能 ~~(毕竟一章漫画太小了，好像也没什么必要，断了不如重下)~~，所以请确保不要在下载中途关闭！**
  - 如果程序意外中断，可以选择把下了一半的文件都删掉(一般在目标漫画文件夹的根目录下)，重新下载
- **程序缓存和日志历史文件存在 `C:\Users\AppData\Roaming\BiliBili-Manga-Downloader\` 目录下，可以通过"清空用户数据"功能一键删除**
- **如果想用"本地库存"功能，需要注意的是：下载好的漫画的文件夹名以及章节名都不能更改，否则将会无法正确读取漫画数据**
- **🔥 下面我要隆重的推荐一款搭配本软件使用的漫画浏览器 ~~(可以说就是为了这点儿醋 我才包的这顿饺子)~~**
  - <div align=center><img src="https://user-images.githubusercontent.com/72005386/222974497-18b568e7-5b2e-416f-8d14-22ec68323570.png" width=100%></div>
  - **NeeView** 是一款 Windows 下开源的图片浏览器，其特色是可以像翻书一样同时浏览两张照片，还支持压缩包看图、鼠标手势、触摸操作、多线程和超前查看、支持 PDF / 视频。 原生支持中文
  - 下载地址: [Microsoft Store](https://www.microsoft.com/en-us/p/neeview/9p24z53hc1jr)
  - 上面是官方介绍，要我说优势就下面几点
    - 自动切页，双页浏览
    - 左右或者右左的阅读顺序一键切换
    - 鼠标左键长摁放大，自由移动放大聚焦点，滚轮调整放大倍数， 这点超爽的好嘛，吊打所有网页浏览体验 ~~(尤其是某些地方需要放大好好品鉴的时候，嗯嗯，我说的就是背景人物！)~~
    - 优秀的资源浏览器以及简明的操作逻辑和界面
    - 总之是电脑端看漫画的不二之选~
  - 唯一的缺点好像就是对条漫不太支持，也有可能是我没找到选项，有知道的小伙伴可以联系我，谢啦~

## 💡 TODO List ~~(在可见的未来...)~~
- **PS: 也欢迎小伙伴们多多的在Issues里提意见，不管是Bug还是操作逻辑，界面优化等等作者统统笑纳~**
  - 🟦 缓存更多资源，减少网络请求
  - 🟦 添加二维码扫码登入功能
  - 🟦 添加不同的界面主题
  - 🟦 添加一个启动程序加载进度条
  - 🟦 添加我的追漫界面，以及追漫功能
  - 🟦 下载任务的暂停和继续功能，断点续传。以及下载任务的持久化，本地缓存
  - 🟦 对于有特典的漫画，提供特典下载界面
- **已解决**
  - ✅ ~~添加检测cookie无效或者过期功能，并且弹窗~~
  - ✅ ~~鼠标移动到漫画封面改变鼠标图标，提示用户可以点击跳转~~
  - ✅ ~~给章节详情添加一个提示，告诉用户可以右键多选~~
  - ✅ ~~除pdf以外添加不同的保存选项如 7z 或者 基本的文件夹图片~~
  - ✅ ~~启动程序时多线程加载本地库存，避免用户等待太久~~
  - ✅ ~~给打包好的程序添加版本号版权等属性信息~~
  - ✅ ~~因为网络错误跳过任务后，更新总进度条的进度，速度和剩余时间信息~~


## 🏗️ 本地构建 / 编译
- **首先确保你安装了 Python >= 3.11 和 git**
- **本项目使用了 pipenv 依靠虚拟环境进行依赖项管理，所以不必担心影响自己的本地环境**
- **作者已经贴心的帮后来者们准备好了两个集成脚本~**
- **接下来的操作都在项目的根目录运行命令行指令**
- **构建项目**
  1. 执行 `git clone https://github.com/Zeal-L/BiliBili-Manga-Downloader.git`
  2. 执行 `cd BiliBili-Manga-Downloader/`
  3. 执行 `sh setup.sh` 等待项目构建完成
  4. 执行 `pipenv shell` 进入虚拟环境
  5. 执行 `python3 app.py` 即可运行程序
- **打包编译**
  1. 执行 `sh build.sh` 等待项目打包完成
  2. 这一步可能会花费一定时间，中途需要手动确认安全漏洞检查
  2. 打包好的程序会被移动到项目的根目录 "哔哩哔哩漫画下载器.exe"
- **彻底清除项目 ~~(删库跑路)~~**
  1. 执行 `pipenv uninstall --all`
  2. 执行 `pipenv --rm `
  3. 执行 `cd .. && rm -rf BiliBili-Manga-Downloader/`

## 🔨 Issues / PR 格式
- **Issues**
  - 正确的标记 Issue Label
  - 标注你的系统环境
  - 问题简介与复现条件
  - 找到日志文件并截取错误信息

- **PR**
  - 遵循项目已有代码的 python doc 格式
  - 明确的注释信息
  - 正确的函数类型声明
  - 在可能出错的IO/网络申请等部分都加上retry装饰器
  - 在需要的地方写入logger日志，格式参考已有代码
  - 更改 / 新增 的功能说明，理由
  - 是否更改依赖性

## ⚰️ 更新记录
### v1.0.3 - *2022-03-12*
- 修复bug：使用7z保存时可能会因为文件名特殊字符引起报错；添加针对“.”的正则过滤
- 优化配置：全局网络请求的 timeout 以及 max retry 值增大一倍

### v1.0.2 - *2022-03-11*
- 修复bug：总进度条数值错误更新为0
- 优化设置选项：以防在网络不好的情况下高线程数导致的频繁重试警告，最大线程数现在设为32

### v1.0.1 - *2022-03-9*
- 优化UI视觉：因为网络错误跳过任务后，更新总进度条的进度，速度和剩余时间信息
- 更新关于界面：添加了作者的联系方式

### v1.0.0 - *2022-03-6*
- 第一个正式版本
- 所有基本功能都测试可用

## 🍻 联系方式
欢迎进群讨论程序，漫画，资源分享, 提交问题等等
- Q群号：244029317

## 🙈 PS
- **做项目不易，求星星！求赞助！如果本项目对你有帮助，请作者喝杯☕吧~**

<img src="https://user-images.githubusercontent.com/72005386/223096480-8d57ceef-0b33-4653-86bf-55e6094fcb9b.jpg" width=20%> <img src="https://user-images.githubusercontent.com/72005386/223096520-e5d95ac8-044d-4644-8500-3770e5ad81f8.jpg" width=18.5%>

## 🔒️ 许可协议
- 本项目使用 [**GNU Affero General Public License v3.0**](https://www.gnu.org/licenses/agpl-3.0.en.html) 发布
- 如对代码有所修改，请按照许可协议要求发布
- 本程序仅供学习交流使用，严禁用于商业用途



