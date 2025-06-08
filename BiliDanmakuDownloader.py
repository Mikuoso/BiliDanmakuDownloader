import sys
import zlib
import time
import csv
import requests
import logging
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
import dm_pb2 as danmaku


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
SAVE_CSV = True  # 是否生成CSV
CSV_OUTPUT_DIR = Path(r"C:csv\output\dir")  # CSV输出目录
CSV_FILENAME = f"P{PART_INDEX}.csv"  # CSV文件名

# XML输出配置
XML_OUTPUT_DIR = Path(r"C:xml\output\dir")  # XML输出目录
XML_FILENAME = f"P{PART_INDEX}.xml"  # XML文件名
# ————————————————————————————————————————————————

# ————————————————————日志配置区————————————————————
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s]%(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
# ————————————————————————————————————————————————


def get_video_info(bvid: str) -> dict:
    """获取视频元数据（cid/avid）"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": COOKIE
    }

    for _ in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()['data']

            # 获取所有分P信息
            pages = data['pages']
            if PART_INDEX > len(pages) or PART_INDEX < 1:
                raise ValueError(f"无效的分P序号，该视频共有 {len(pages)} 个分P")

            # 获取指定分P信息
            selected_page = pages[PART_INDEX - 1]
            return {
                "oid": selected_page['cid'],
                "pid": data['aid'],
                "title": f"{data['title']} - {selected_page['part']}"
            }
        except Exception as e:
            logging.error(f"获取视频信息失败: {e}")
            time.sleep(REQUEST_INTERVAL)
    raise RuntimeError("无法获取视频信息")


def get_all_danmaku(oid: int, pid: int) -> list:
    """获取所有分段的弹幕数据"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Referer": f"https://www.bilibili.com/video/{BVID}",
        "Cookie": COOKIE
    }

    all_danmaku = []
    segment = 1

    while True:
        logging.info(f"正在获取第 {segment} 段弹幕...")
        params = {
            "type": 1,
            "oid": oid,
            "pid": pid,
            "segment_index": segment
        }

        # 请求重试
        for retry in range(MAX_RETRIES):
            try:
                resp = requests.get(
                    "https://api.bilibili.com/x/v2/dm/web/seg.so",
                    params=params,
                    headers=headers,
                    timeout=15
                )
                resp.raise_for_status()
                break
            except Exception as e:
                if retry == MAX_RETRIES - 1:
                    logging.warning(f"第 {segment} 段请求失败，终止获取")
                    return all_danmaku
                logging.warning(f"请求失败，第 {retry + 1} 次重试...")
                time.sleep(REQUEST_INTERVAL)

        # 处理压缩数据
        try:
            data = zlib.decompress(resp.content)
        except zlib.error:
            data = resp.content

        # 解析Protobuf
        try:
            danmaku_seg = danmaku.DmSegMobileReply()
            danmaku_seg.ParseFromString(data)
        except Exception as e:
            logging.error(f"解析失败: {e}")
            logging.error("错误数据头部:", data[:16].hex())
            break

        # 获取当前段弹幕数量
        count = len(danmaku_seg.elems)
        logging.info(f"成功获取 {count} 条弹幕")
        if count == 0:
            logging.info(f"第 {segment} 段无新弹幕，终止获取")  # 新增提示
            break  # 终止循环
        all_danmaku.extend(danmaku_seg.elems)
        segment += 1
        time.sleep(REQUEST_INTERVAL)

    # 添加总弹幕数到日志
    logging.info(f"已获取所有弹幕分段，总弹幕数：{len(all_danmaku)}")  # 修改此行
    return all_danmaku


def save_as_csv(danmaku_list: list, filename: str):
    """保存完整弹幕数据到CSV"""
    fields_order = [
        ("id", "弹幕ID"),
        ("progress", "出现时间(毫秒)"),
        ("mode", "模式"),
        ("fontsize", "字体大小"),
        ("color", "颜色"),
        ("midHash", "用户MID哈希"),
        ("content", "内容"),
        ("ctime", "发送时间"),
        ("weight", "权重"),
        ("action", "动作"),
        ("pool", "弹幕池"),
        ("idStr", "弹幕ID字符串"),
        ("attr", "属性"),
        ("animation", "动画")
    ]

    try:
        with open(filename, "w", encoding="utf-8-sig", newline='') as f:
            writer = csv.writer(f)
            # 写入元数据
            writer.writerow(["视频标题", video_info['title']])
            writer.writerow(["视频BV号", BVID])
            writer.writerow(["分P序号", PART_INDEX])
            writer.writerow(["弹幕总数", len(danmaku_list)])
            writer.writerow(["导出时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])
            # 写入列标题
            writer.writerow([col for _, col in fields_order])
            # 写入数据行
            for d in danmaku_list:
                row = []
                for field in [field for field, _ in fields_order]:
                    try:
                        value = getattr(d, field)
                        # 特殊字段处理
                        if field == "color":
                            value = f"#{value:06x}"
                        elif field == "ctime":
                            value = datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
                        elif field == "weight":
                            value = max(0, min(int(value), 10))
                        elif field == "attr":
                            attr_value = int(value)
                            attributes = []
                            if attr_value & (1 << 0): attributes.append("保护")
                            if attr_value & (1 << 1): attributes.append("直播")
                            if attr_value & (1 << 2): attributes.append("高赞")
                            value = ",".join(attributes) if attributes else "普通"
                        row.append(str(value))
                    except AttributeError:
                        row.append("N/A")
                writer.writerow(row)
    except Exception as e:
        logging.error(f"CSV保存失败: {str(e)}")


def generate_xml(danmaku_list: list, output_path: Path):
    """生成标准XML弹幕文件"""
    root = ET.Element("i")
    processed_count = 0
    for d in danmaku_list:

        # 用户过滤
        if TARGET_USER_MIDHASH and d.midHash != TARGET_USER_MIDHASH:
            continue

        # 构建属性参数
        p_params = [
            f"{d.progress / 1000:.5f}",  # 出现时间（秒）
            str(d.mode),                 # 弹幕类型
            str(d.fontsize),             # 字体大小
            str(d.color),                # 颜色（十进制）
            str(d.ctime),                # 创建时间（保留字段）
            str(d.pool),                 # 弹幕池
            d.midHash,                   # 用户mid哈希
            d.idStr,                     # 弹幕ID字符串
            str(max(0, min(d.weight, 10)))  # 权重
        ]

        # 创建弹幕节点
        danmaku_elem = ET.Element("d")
        danmaku_elem.set("p", ",".join(p_params))
        danmaku_elem.text = d.content
        root.append(danmaku_elem)
        processed_count += 1

    # 生成XML内容
    xml_str = ET.tostring(root, encoding="utf-8").decode()
    xml_content = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_content)
        logging.info(f"XML文件已生成，共处理 {processed_count} 条弹幕")
    except Exception as e:
        logging.error(f"XML保存失败: {str(e)}")


if __name__ == "__main__":
    # 确保输出目录存在
    Path(CSV_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(XML_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    try:
        # 获取视频元数据
        video_info = get_video_info(BVID)
        logging.info(f"视频信息获取成功: {video_info['title']}")

        # 获取弹幕数据
        danmaku_list = get_all_danmaku(video_info["oid"], video_info["pid"])
        if not danmaku_list:
            raise RuntimeError("未获取到有效弹幕数据")

        # 生成完整输出路径
        csv_path = CSV_OUTPUT_DIR / CSV_FILENAME
        xml_path = XML_OUTPUT_DIR / XML_FILENAME

        # 保存CSV
        if SAVE_CSV:
            save_as_csv(danmaku_list, str(csv_path))
            logging.info(f"CSV文件已保存至: {csv_path}")

        # 生成XML（自动处理用户过滤）
        generate_xml(danmaku_list, xml_path)
        logging.info(f"XML文件已保存至: {xml_path}")

    except Exception as e:
        logging.error(f"程序运行失败: {str(e)}")
        sys.exit(1)
    finally:
        logging.info("程序执行完毕")