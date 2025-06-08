# BiliDanmakuDownloader B站弹幕下载器2.0

本项目为[BiliDMProtobufDownloader](https://github.com/Mikuoso/BiliDMProtobufDownloader)与[ProtobufCSV2XML](https://github.com/Mikuoso/ProtobufCSV2XML)的合并版本，现已完成合并工作！  
本工具基于Python 3.10，使用Protobuf方式获取指定的B站视频的弹幕数据，导出XML格式，并提供用户过滤功能，同时允许导出完整弹幕数据（CSV格式）。
## 📖 特别声明
本项目开发过程中参考了[SocialSisterYi/bilibili-API-collect](https://github.com/SocialSisterYi/bilibili-API-collect)的实现思路，感谢各位大佬的贡献！  
源项目遵循 CC BY-NC 4.0 协议，禁止一切商业使用！！！  
参考文档：[Protobuf弹幕](https://socialsisteryi.github.io/bilibili-API-collect/docs/danmaku/danmaku_proto.html)。

## 🎯 功能特性  
- ✅ 支持BV号视频解析  
- ✅ 支持多分P视频选择  
- ✅ 完整弹幕数据导出（CSV格式），包含颜色、发送时间、用户哈希等15+个字段
- ✅ 自动解压zlib压缩的Protobuf数据 
- ✅ 标准XML弹幕文件生成  
- ✅ 指定用户弹幕过滤  

## 🚀 快速开始
### 📦 依赖安装
1. 安装依赖库：
```bash
# 安装必要的依赖库
pip install requests protobuf
```
2. 编译proto定义：
```bash
protoc --python_out=. dm.proto
```
### 🌱 使用方法
1. 修改用户配置区配置参数
2. 运行脚本
## ⚙️ 配置说明
```python
# ————————————————————用户配置区————————————————————
# 输入配置
BVID = "BV1VuZ5YjEin"  # 替换为要下载的视频BV号
PART_INDEX = 3  # 分P序号（从1开始计数）
COOKIE = ("SESSDATA=YourSESSDATA;"
          "bili_jct=Yourbili_jct")  # 替换为真实Cookie
REQUEST_INTERVAL = 1  # 请求间隔（秒）
MAX_RETRIES = 3  # 失败重试次数

# 输出配置
TARGET_USER_MIDHASH = "abcd1234"    # 指定用户midHash，留空则转换全部

# CSV输出配置
SAVE_CSV = True  # 是否生成CSV（True/False）
CSV_OUTPUT_DIR = Path(r"C:csv\output\dir")  # CSV输出目录
CSV_FILENAME = f"P{PART_INDEX}.csv"  # CSV文件名

# XML输出配置
XML_OUTPUT_DIR = Path(r"C:xml\output\dir")  # XML输出目录
XML_FILENAME = f"P{PART_INDEX}.xml"  # XML文件名
```

## 输出文件实例
### CSV格式
```CSV
视频标题,【高清修复】东方幻想万华镜全集 - 3-红雾异变之章中篇
视频BV号,BV1VuZ5YjEin
分P序号,3
弹幕总数,4645
导出时间,2025-06-08 12:34:56

弹幕ID,出现时间(毫秒),模式,字体大小,颜色,用户MID哈希,内容,发送时间,权重,动作,弹幕池,弹幕ID字符串,属性,动画
1849144832451793920,507494,1,25,#e70013,e6a644fc,[前方高能],2025/5/18 8:00,10,picture:i0.hdslb.com/bfs/feed-admin/bd90726bb0c982c161eab7ad67e8460258a8959c.png?scale=1.00,0,1849144832451793920,普通,"{"id":20004,"cid":0,"advanced_block":0,"animation_attr":0,"mime":"image","resource":"i0.hdslb.com/bfs/feed-admin/bd90726bb0c982c161eab7ad67e8460258a8959c.png","scale":1}"
```
### XML格式
```XML
<i>
  <d p="507.49400,1,25,15138835,1747539664,0,e6a644fc,1849255749982165504,10">测试弹幕</d>
</i>
```

## 📌 注意事项
### Cookie获取：
网页端登录Bilibili后通过`F12开发者工具`获取  
包含`SESSDATA`和`bili_jct`字段  
**格式示例**：SESSDATA=abc123; bili_jct=def456  
**另外 需要注意的是：**
- 部分视频在无`Cookie: SESSDATA`时只返回部分弹幕。  
- 只能返回普通弹幕`（pool=1 mode=1-7）`和代码弹幕`（pool=2 mode=8）`。

### midHash获取：
通过弹幕CSV文件中的`用户MID哈希`列获取
留空则导出全部用户弹幕

### Proto文件编译：
需要安装protobuf编译器
使用提供的`dm.proto`生成Python文件

## ✨ 更新计划
本项目最初是为《【高清修复】东方幻想万华镜全集》补档工作而设计，尽管现已结束补档工作，但本项目将继续作为练手作继续练习开发、维护。
