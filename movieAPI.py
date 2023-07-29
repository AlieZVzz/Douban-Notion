import time
from notion_database.properties import Properties
from notion_database.database import Database
from notion_database.page import Page
import requests
from bs4 import BeautifulSoup
import re

databaseid = '9c4b15b3675d439680c87cb3a1e50873'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Cookie': 'll="108288"; bid=LxuBFcq903Y; _pk_id.100001.8cb4=d9ac29ae35fdb232.1687791343.; _pk_ses.100001.8cb4=1; __utma=30149280.453255204.1687791344.1687791344.1687791344.1; __utmc=30149280; __utmz=30149280.1687791344.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; dbcl2="208462734:1M1epG+m4oE"; ck=O7sa; push_noty_num=0; push_doumail_num=0; __utmv=30149280.20846; __utmb=30149280.5.9.1687791368060; ap_v=0,6.0',
    # 'Host': 'www.douban.com',
    'Content-type': 'text/html; charset=utf-8',
    # 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Upgrade-Insecure-Requests': '1',
    # 'Accept-Encoding': 'gzip, deflate, br'
}
rss_address = "https://www.douban.com/feed/people/208462734/interests"
notion_api = "Bearer secret_4aA1JcVQKjF1RlunDeKhlaUWCrkO4By4BUY8jJynckw"


def film_info2(movie_url):
    # 目前想改进的有title，类型，导演
    if "http://" in movie_url:
        movie_url= movie_url.replace("http://","https://")
    url = movie_url
    res = requests.get(url, headers=headers, allow_redirects=False)
    url = res.headers['Location'] if res.status_code == 302 else url
    print(url)
    res = requests.get(url, headers=headers, allow_redirects=False)
    bstitle = BeautifulSoup(res.text, 'html.parser')

    moive_content = bstitle.find_all('div', id='content')
    moive_content = moive_content[0]
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
    pattern_director = re.compile(r'(?<=导演: )[\u4e00-\u9fa5^a-z^A-Z· ]+', re.I)
    if len(re.findall(pattern_director, info))>0:
        director = re.findall(pattern_director, info)[0].replace(" ", "").split("/")
    # print(director)
    else:
        director = "aaa"
    # print(director)

    return title, movie_type, director




def download_picture(url):
    headers = {
        "Host": "movie.douban.com",
        "Referer": "https://movie.douban.com/top250?start=225&filter=",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    }
    # 获取网页的源代码
    r = requests.get(url, headers=headers)
    # 利用BeautifulSoup将获取到的文本解析成HTML
    soup = BeautifulSoup(r.text, "lxml")
    # 获取网页中的电影图片
    content = soup.find('div', class_='article')
    if content is None:
        return ""
    images = content.find_all('img')
    # 获取电影图片的名称和下载地址
    # picture_name_list = [image['alt'] for image in images]
    picture_link_list = images[0]['src']

    # 利用urllib.request..urlretrieve正式下载图片
    # for picture_name, picture_link in zip(picture_name_list, picture_link_list):
    #     urllib.request.urlretrieve(picture_link, 'E://douban/%s.jpg' % picture_name)
    return picture_link_list


def updateMovieType(database_id):
    P = Page(integrations_token="secret_wa5Mmdai45S2vBpXXr1Hkx8eATxKQVGTydscWBstPsG")
    D = Database(integrations_token="secret_wa5Mmdai45S2vBpXXr1Hkx8eATxKQVGTydscWBstPsG")
    D.find_all_page(database_id=database_id)
    while D.result["has_more"]:
        firms = D.result["results"]
        for i in firms:
            # print(i)
            time.sleep(0.5)
            try:
                P.retrieve_page(page_id=i["id"])
                url = P.result["properties"]["影片链接"]["url"]
                type = P.result["properties"]['类型']["multi_select"]
            
                title = P.result["properties"]["名称"]["title"][0]["text"]["content"]
                _, genre, director = film_info2(url)
                PROPERTY = Properties()
                PROPERTY.set_multi_select("类型", text_list=genre)
                PROPERTY.set_multi_select("导演", text_list=director)
                P.update_page(page_id=i["id"], properties=PROPERTY)
            except:
                print("update failed")
            print("update success    " + title)
        D.find_all_page(database_id=database_id, start_cursor=D.result["next_cursor"], page_size=200)
    print("update completed")


def updateMovieUrl(database_id, movie_dict):
    P = Page(integrations_token="secret_wa5Mmdai45S2vBpXXr1Hkx8eATxKQVGTydscWBstPsG")
    D = Database(integrations_token="secret_wa5Mmdai45S2vBpXXr1Hkx8eATxKQVGTydscWBstPsG")
    D.find_all_page(database_id=database_id)
    while D.result["has_more"]:
        
        firms = D.result["results"]
        for i in firms:
            time.sleep(1)
            P.retrieve_page(page_id=i["id"])
            url = P.result["properties"]["影片链接"]["url"]
            if not url:
                title = P.result["properties"]["名称"]["title"][0]["text"]["content"]
                for key in movie_dict["标题"]:
                    if movie_dict["标题"][key] in title:
                        new_url = movie_dict["链接"][key]
                        PROPERTY = Properties()
                        PROPERTY.set_url("影片链接", text=new_url)
                        print("update success    " + title)
                        P.update_page(page_id=i["id"], properties=PROPERTY)
            else:
                print("skip")
            D.find_all_page(database_id=database_id, start_cursor=D.result["next_cursor"], page_size=200)

    

def updateMovieCover(database_id):
    P = Page(integrations_token="secret_wa5Mmdai45S2vBpXXr1Hkx8eATxKQVGTydscWBstPsG")
    D = Database(integrations_token="secret_wa5Mmdai45S2vBpXXr1Hkx8eATxKQVGTydscWBstPsG")
    D.find_all_page(database_id=database_id)
    while D.result["has_more"]:
        firms = D.result["results"]
        for i in firms:
            # print(i)
            time.sleep(1)
            P.retrieve_page(page_id=i["id"])
            if len(P.result["properties"]["封面"]["files"]) == 0:
                url = P.result["properties"]["影片链接"]["url"]
                cover = download_picture(url)
                if cover != "":
                    PROPERTY = Properties()
                    PROPERTY.set_files("封面", files_list=[cover])
                    P.update_page(page_id=i["id"], properties=PROPERTY)
                    print("update success   " + cover)
            else:
                print("skip")
    D.find_all_page(database_id=database_id, start_cursor=D.result["next_cursor"], page_size=200)