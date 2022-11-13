import NotionAPI
import requests
from bs4 import BeautifulSoup
import time
import re
from config import *

def DataBase_additem(database_id, body_properties, station):
    body = {
        'parent': {'type': 'database_id', 'database_id': database_id},
    }
    body.update(body_properties)

    url_notion_additem = 'https://api.notion.com/v1/pages'
    notion_additem = requests.post(url_notion_additem, headers=headers, json=body)

    if notion_additem.status_code == 200:
        print(station + '·更新成功')
    else:
        print(station + '·更新失败')


def film_info2(movie_url):
    # 目前想改进的有title，类型，导演

    url = movie_url
    res = requests.get(url, headers=headers)
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
    director = re.findall(pattern_director, info)[0].replace(" ", "").split("/")
    # print(director)

    return title, movie_type, director


def download_picture(url):
    headers = {
        "Host": "movie.douban.com",
        "Referer": "https://movie.douban.com/top250?start=225&filter=",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36",
    }
    # 获取网页的源代码
    r = requests.get(url, headers=headers)
    # 利用BeautifulSoup将获取到的文本解析成HTML
    soup = BeautifulSoup(r.text, "lxml")
    # 获取网页中的电影图片
    content = soup.find('div', class_='article')
    images = content.find_all('img')
    # 获取电影图片的名称和下载地址
    # picture_name_list = [image['alt'] for image in images]
    picture_link_list = images[0]['src']

    # 利用urllib.request..urlretrieve正式下载图片
    # for picture_name, picture_link in zip(picture_name_list, picture_link_list):
    #     urllib.request.urlretrieve(picture_link, 'E://douban/%s.jpg' % picture_name)
    return picture_link_list



notion_moives = NotionAPI.DataBase_item_query(databaseid)
for item in notion_moives:
    print(item)
    # title = item['properties']['名称']['title'][0]['plain_text']
    watch_time = item['properties']['观看时间']['date']['start']
    movie_url = item['properties']['影片链接']['url']
    comment = ''
    title, movie_type, director = film_info2(movie_url)
    cover_url = download_picture(movie_url)
    score = "⭐⭐"
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
                                 {'type': 'text', 'text': {'content': str(comment)}, 'plain_text': str(comment)}]},
            '影片链接': {'type': 'url', 'url': str(movie_url)},
            '类型': {'type': 'multi_select', 'multi_select': [{'name': str(itemm)} for itemm in movie_type]},
            '导演': {'type': 'multi_select', 'multi_select': [{'name': str(itemm)} for itemm in director]},

        }
    }
    print(body)
    NotionAPI.DataBase_additem(databaseid, body, title)
    time.sleep(3)
