import feedparser
import requests
from bs4 import BeautifulSoup
import re
import NotionAPI
import time
from config import *


def film_info1(item):
    # 名称title 封面链接cover_url 观影时间watch_time 电影链接movive_url 评分score 评论 comment
    pattern1 = re.compile(r'(?<=src=").+(?=")', re.I)  # 匹配海报链接
    title = item["title"].split("看过")[1]
    # print(title)
    cover_url = re.findall(pattern1, item["summary"])[0]
    cover_url = cover_url.replace("s_ratio_poster", "r")
    # print(cover_url)
    # 类型
    # 导演
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
    # print(item["summary"])
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
    # 目前想改进的有title，类型，导演

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
    # print(info)
    pattern_type = re.compile(r'(?<=类型: )[\u4e00-\u9fa5 /]+', re.S)
    movie_type = re.findall(pattern_type, info)[0].replace(" ", "").split("/")
    # print(movie_type)
    pattern_director = re.compile(r'(?<=导演: )[\u4e00-\u9fa5 /]+', re.I)
    # print(re.findall(pattern_director, info))
    if len(re.findall(pattern_director, info))>0:
        director = re.findall(pattern_director, info)[0].replace(" ", "").split("/")
    # print(director)
    else:
        director = ""

    return title, movie_type, director


# 开始连接notion

# 改进：加入重试机制，加入防止重复
if __name__ == '__main__':

    # notion相关配置

    rss_movietracker = feedparser.parse(rss_address,
                                        request_headers=headers)
    print(rss_movietracker)
    # item = rss_movietracker["entries"][1]
    notion_moives = NotionAPI.DataBase_item_query(databaseid)
    watched_movie = [item['properties']['影片链接']['url'] for item in notion_moives]
    print(watched_movie)
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
            NotionAPI.DataBase_additem(databaseid, body, title)
            time.sleep(3)
