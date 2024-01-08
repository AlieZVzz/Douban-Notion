import time
import yaml
import os
import re
import feedparser
import requests
from bs4 import BeautifulSoup
import NotionAPI
from PIL import Image


def compress_image(input_path, max_size_kb=5000):
    """
    压缩图片
    :param input_path:
    :param max_size_kb:
    :return:
    """
    with Image.open(input_path) as img:
        width, height = img.size
        file_size = os.path.getsize(input_path) / 1024  # 转换为KB
        if file_size > max_size_kb:
            compression_ratio = (max_size_kb / file_size) ** 0.5
            new_width = int(width * compression_ratio)
            new_height = int(height * compression_ratio)
            compressed_img = img.resize((new_width, new_height))
            compressed_img.save(input_path)
        else:
            img.save(input_path)


def download_img(img_url):
    """
    download douban cover to local
    :param img_url:
    :return:
    """
    r = requests.get(img_url, headers={'Referer': 'http://movie.douban.com'}, stream=True)
    img_name = "posters/" + img_url.split("/")[-1]
    if r.status_code == 200:
        with open("posters/" + img_url.split("/")[-1], 'wb') as f:
            for chunk in r.iter_content(chunk_size=2048):
                if chunk:
                    f.write(chunk)
                    f.flush()
    return img_name


def upload_img(path):
    """
    upload img to smms
    :param path:
    :return:
    """
    compress_image(path)
    headers = {'Authorization': config["smms_token"]}
    files = {'smfile': open(path, 'rb')}
    url = 'https://sm.ms/api/v2/upload'
    res = requests.post(url, files=files, headers=headers)
    res = res.json()

    if "data" in res.keys():
        return res['data']['url']


def film_info1(item):
    """名称title 封面链接cover_url 观影时间watch_time 电影链接movive_url 评分score 评论 comment"""
    pattern1 = re.compile(r'(?<=src=").+(?=")', re.I)  # 匹配海报链接
    title = item["title"].split("看过")[1]
    cover_url = re.findall(pattern1, item["summary"])[0]
    cover_url = cover_url.replace("s_ratio_poster", "r")

    img_file = download_img(cover_url)
    cover_url = upload_img(img_file)

    time = item["published"]
    pattern2 = re.compile(r'(?<=. ).+\d{4}', re.S)  # 匹配时间
    month_satandard = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
                       'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    time = re.findall(pattern2, time)[0]
    time = time.split(" ")
    day = time[0]
    month = month_satandard[time[1]]
    year = time[2]
    watch_time = str(year) + "-" + str(month) + "-" + str(day)
    # print(watch_time)

    movie_url = item["link"]

    # 处理comment
    pattern = re.compile(r'(?<=<p>).+(?=</p>)', re.S)  # 匹配评论·
    # pattern2 = re.compile(r'(?<=<p>)(.|\n)+(?=</p>)', re.I) # 匹配评论·
    allcomment = re.findall(pattern, item["summary"])[0]  # 需要进一步处理
    # print(allcomment)

    pattern1 = re.compile(r'(?<=推荐: ).+(?=</p>)', re.S)  # 匹配评分
    # 一星：很差 二星：较差 三星：还行 四星：推荐 五星：力荐
    scoredict = {'很差': '⭐', '较差': '⭐⭐', '还行': '⭐⭐⭐', '推荐': '⭐⭐⭐⭐', '力荐': '⭐⭐⭐⭐⭐', }
    # score = re.findall(pattern1, allcomment)
    score = allcomment[-2:]
    if score:
        score = scoredict[score]
    else:
        score = "⭐⭐⭐"
    # print(score)

    # pattern2 = re.compile(r'(?<=<p>).+', re.S)  # 匹配评价
    # comment = re.findall(pattern2, allcomment)[0]
    # comment = comment.split("备注: ")[1]
    comment = ''
    return cover_url, watch_time, movie_url, score, comment


def film_info2(movie_url):

    url = movie_url[:4] + 's' + movie_url[4:]
    res = requests.get(url, headers=headers)
    print(res)
    bstitle = BeautifulSoup(res.text, 'html.parser')

    moive_content = bstitle.find_all('div', id='content')[0]

    # 电影名称与年份
    title = moive_content.find('h1')
    title = title.find_all('span')
    title = title[0].text + title[1].text

    # 电影名称与年份
    title = moive_content.find('h1')
    title = title.find_all('span')
    title = title[0].text + title[1].text

    # 基本信息
    base_information = moive_content.find('div', class_='subject clearfix')
    info = base_information.find('div', id='info').text.split('\n')
    info = ','.join(info)

    pattern_type = re.compile(r'(?<=类型: )[\u4e00-\u9fa5 /]+', re.S)
    movie_type = re.findall(pattern_type, info)[0].replace(" ", "").split("/")
    pattern_director = re.compile(r'(?<=导演: )[\u4e00-\u9fa5 /]+', re.I)

    if len(re.findall(pattern_director, info)) > 0:
        director = re.findall(pattern_director, info)[0].replace(" ", "").split("/")
    # print(director)
    else:
        director = ""

    return title, movie_type, director


# 开始连接notion

# 改进：加入重试机制，加入防止重复
if __name__ == '__main__':
    fs = open(os.path.join("./", "config.yaml"), encoding="UTF-8")
    config = yaml.safe_load(fs)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Cookie': 'll="108288"; bid=LxuBFcq903Y; _pk_id.100001.8cb4=d9ac29ae35fdb232.1687791343.; _pk_ses.100001.8cb4=1; __utma=30149280.453255204.1687791344.1687791344.1687791344.1; __utmc=30149280; __utmz=30149280.1687791344.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; dbcl2="208462734:1M1epG+m4oE"; ck=O7sa; push_noty_num=0; push_doumail_num=0; __utmv=30149280.20846; __utmb=30149280.5.9.1687791368060; ap_v=0,6.0',
        # 'Host': 'www.douban.com',
        'Content-type': 'text/html; charset=utf-8',
        # 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Upgrade-Insecure-Requests': '1',
        # 'Accept-Encoding': 'gzip, deflate, br'
    }

    # notion相关配置

    rss_movietracker = feedparser.parse(config["rss_address"],
                                        request_headers=headers)
    print(rss_movietracker)
    # item = rss_movietracker["entries"][1]
    notion_moives = NotionAPI.DataBase_item_query(config["databaseid"])
    watched_movie = [item['properties']['影片链接']['url'] for item in notion_moives]
    # print(watched_movie)
    for item in rss_movietracker["entries"]:
        if "看过" not in item["title"]:
            continue
        cover_url, watch_time, movie_url, score, comment = film_info1(item)

        rel = NotionAPI.select_items_form_Databaseitems(notion_moives, "影片链接", movie_url)
        if rel:
            continue

        if movie_url not in watched_movie:
            title, movie_type, director = film_info2(movie_url)

            body = {
                'properties': {
                    '名称': {
                        'title': [{'type': 'text', 'text': {'content': str(title)}}]
                    },
                    '观看时间': {'date': {'start': str(watch_time)}},
                    '评分': {'type': 'select', 'select': {'name': str(score)}},
                    '封面': {
                        'files': [{'type': 'external', 'name': '封面', 'external': {'url': str(cover_url)}}]
                    },
                    '有啥想说的不': {'type': 'rich_text',
                                     'rich_text': [
                                         {'type': 'text', 'text': {'content': str(comment)},
                                          'plain_text': str(comment)}]},
                    '影片链接': {'type': 'url', 'url': str(movie_url)},
                    '类型': {'type': 'multi_select', 'multi_select': [{'name': str(itemm)} for itemm in movie_type]},
                    '导演': {'type': 'multi_select', 'multi_select': [{'name': str(itemm)} for itemm in director]},

                }
            }
            print(body)
            NotionAPI.DataBase_additem(config["databaseid"], body, title)
            time.sleep(3)
