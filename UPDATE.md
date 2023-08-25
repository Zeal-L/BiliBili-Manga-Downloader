## ⚰️ 更新记录
### **[v1.3.1](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.3.1)** - *2022-08-25*
- 修复bug:
  - 修复了一个在保存格式为 `pdf` 时导致内存泄漏的bug ([#68][i68])
- 优化:
  - 优化下载速度和剩余时间的计算与获取, 现在更加的平稳和准确了
  - 重构下载任务相关的逻辑，减少耦合性

[i68]: https://github.com/Zeal-L/BiliBili-Manga-Downloader/issues/68

### **[v1.3.0](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.3.0)** - *2022-08-11*
- 新增功能:
  - 二维码登入
  - 利用 [Biliplus](https://www.biliplus.com/) 提供的 [ComicWebReader](https://www.biliplus.com/manga/) 在线漫画平台的api来尝试获取未解锁的漫画章节
- 优化配置:
  - 移除保存文件夹名里的漫画ID信息；元数据现在默认保存，并且以此来初始化我的库存
  - 老用户需要重新下载一章漫画，然后把以前下载好的移动到新文件夹中
- 修复bug:
  - 修复个别`png`保存为`jpg`的情况
  - 修复`BiliPlus Cookie`检测可能出现的隐藏`bug` ([#61][i61])
  - 修复`BiliPlus`可以看未解锁的漫画章节，软件无法下载 ([#52][i52])

[i52]: https://github.com/Zeal-L/BiliBili-Manga-Downloader/issues/52
[i61]: https://github.com/Zeal-L/BiliBili-Manga-Downloader/issues/61

### **[v1.2.0-alpha](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.2.0-alpha)** - *2022-07-4*
- 非生产准备就绪的实验性版本
- 测试 `Biliplus Api`

### **[v1.2.0](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.2.0)** - *2022-06-20*
- 新增功能: 现在可以一键保存漫画的元数据了，包括漫画封面，漫画信息, 等等 (json格式) ([#39][i39])
- 重大优化: 对于 `文件夹-图片形式` 和 `7z压缩包` 的保存方式取消了对漫画原图像的二次压缩，现在图像保存的质量和原图一致。~~（虽然用肉眼看不出来）~~ 由于 `PDF` 保存格式的特殊性，仍然会进行二次压缩和信道转换

[i39]: https://github.com/Zeal-L/BiliBili-Manga-Downloader/issues/39

### **[v1.1.0](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.1.0)** - *2022-05-19*
- 新增功能: 添加了多种主题选择
- 新增功能: 一键检查软件更新
- 修复bug: 修复了一个可能会导致启动失败的保存路径设置；现在如果保存的路径意外失效会初始化为默认路径（cwd）

### **[v1.0.4](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.0.4)** - *2022-04-24*
- 优化使用体验: 我的库存列表现在按照漫画名排序
- 优化项目结构: 重新分类了原始UI文件和资源文件，并更新了打包脚本
- 更新依赖项：更新了过去一个月积攒的 pyside6，pillow 等 python 库的新版本

### **[v1.0.3](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.0.3)** - *2022-03-12*
- 修复bug: 使用7z保存时可能会因为文件名特殊字符引起报错；添加针对“.”的正则过滤
- 优化配置: 全局网络请求的 timeout 以及 max retry 值增大一倍

### **[v1.0.2](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.0.2)** - *2022-03-11*
- 修复bug: 总进度条数值错误更新为0
- 优化设置选项: 以防在网络不好的情况下高线程数导致的频繁重试警告，最大线程数现在设为32

### **[v1.0.1](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.0.1)** - *2022-03-9*
- 优化UI视觉: 因为网络错误跳过任务后，更新总进度条的进度，速度和剩余时间信息
- 更新关于界面: 添加了作者的联系方式

### **[v1.0.0](https://github.com/Zeal-L/BiliBili-Manga-Downloader/releases/tag/v1.0.0)** - *2022-03-6*
- 第一个正式版本
- 所有基本功能都测试可用