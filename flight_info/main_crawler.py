'''
需求：编写一个爬虫，获取今天随后几天所有航班的信息。
思路：
1.通过python的date模块可以很容易的获取当天的日期和未来几天的日期。
2.在城市一览表中将所有城市的代码调取出来放到一个列表中。
3.写一个最基础的爬虫函数，可以通过四个参数（航班日期，出发城市，目的城市）获取页面并解析出页面中的所有信息。
4.将函数封装成多进程爬虫，提高工作效率

'''
import datetime
import pickle
import os
import requests
from bs4 import BeautifulSoup
import time as t
from multiprocessing import Pool,Manager
from Ip_Get_class import IP_GET
import pymysql
from count import Count_info


# 获取今天的日期
today_date = datetime.date.today()
thedate = str(today_date)


#从城市一览表中获取所有城市的编码,存入列表中
thefile = open(os.curdir+os.sep+'城市一览表.pkl','rb')
thedict = pickle.load(thefile)
city_list=list(thedict.values())
city_list.sort()

city_word=list(thedict.values())
city_name=list(thedict.keys())
find_dict = dict(zip(city_word,city_name))


db = pymysql.connect(
    host = 'localhost',
    port = 3306,
    user = 'wenhuan',
    password = 'wen8825994',
    db = 'flight_info',
    charset = 'utf8'
)

cursor = db.cursor()

class Get_web:
    def __init__(self,ip_list,info_list):
        self.ip_list = ip_list
        self.info_list = info_list
    #编写一个可以通过四个参数（航班日期，出发城市，目的城市）获取页面并解析出页面中的所有信息。
    def get_web(self,t_date,city_start,city_aim):
        url = 'http://m.ctrip.com/html5/flight/%s-%s-day-1.html?ddate=%s' % (city_start,city_aim,t_date)
        # 设置代理
        while True:
            try:
                if self.ip_list:
                    ip_m = self.ip_list.pop()
                    ip = r'http://' + ip_m
                    proxies = {'http': ip}
                    print('正在使用代理IP %s ' % ip)
                    web_data = requests.get(url,proxies=proxies,timeout=3)
                    self.ip_list.insert(0,ip_m)
                else:
                    web_data = requests.get(url,timeout=3)
                web_data.encoding = 'utf-8'
                break
            except Exception as e:
                print('由于' + str(e) + '原因，重新启动！')
        soup = BeautifulSoup(web_data.text,'lxml')
        flight_list = soup.select('#j-seo > ul > li.f-arrow-bottom.flight-open-sm.mf-main-cabin')#航班名称
        #print(soup.prettify())
        for i in flight_list:
            start_point = i.select('div.f-dtime > span.f-airPort')[0].get_text()
            start_time = i.select('div.f-dtime > span.f-lst-time')[0].get_text()
            end_point = i.select('div.f-atime > span.f-airPort')[0].get_text()
            end_time = i.select('div.f-atime > span.f-lst-time')[0].get_text()
            price = i.select('span.f-lst-price-num')[0].get_text()
            name = i.select('span.f-lst-no.f-lst-no-1')[0].get_text()
            data = {
                '起点机场':start_point,
                '终点机场': end_point,
                '起点城市': find_dict[city_start],
                '终点城市': find_dict[city_aim],
                '起时': start_time,
                '终时': end_time,
                '票价':price,
                '航班名称': name,
                '航班日期':t_date,
                '取数日期':thedate,
                }

            sql = "INSERT INTO 2017年4月16(航班,出发机场,到达机场,出发日期,出发时间,到达时间,机票价格,统计日期,出发城市,到达城市) " \
                  "VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')" % (data['航班名称'],data['起点机场'],data['终点机场'],data['航班日期'],data['起时'],data['终时'],data['票价'],data['取数日期'],data['起点城市'],data['终点城市'])
            cursor.execute(sql)
            db.commit()
            self.info_list.put(data)

if __name__ == '__main__':
    #写一个函数，获取今日之后的几天的日期，并返回一个列表
    def date_list(n):
        the_list = []
        for i in range(n):
            i_date = today_date + datetime.timedelta(i)
            the_list.append(str(i_date))
        return the_list


    pool = Pool()
    # 构造一个函数，创建列表装载目标函数的参数,构造的函数有一个日期参数
    def get_aim_list(t_date):
        aim_list = []
        num = len(city_list)
        for i in range(num):
            for j in range(i+1,num):
                aim_list.append((t_date,city_list[i],city_list[j]))
        return aim_list

    #构建代理池
    IP_POOL = []
    ip_pl = IP_GET(IP_POOL,10)
    ip_pl.start()
    #构建数据库
    manager = Manager()
    out_queue = manager.Queue()
    the_get = Get_web(IP_POOL,out_queue)
    #引入计数类对象，计算数据库的实时容量
    the_count = Count_info('que',out_queue)
    the_count.start()

    #开始执行多进程
    sta_t = t.clock()
    for i in date_list(10):
        pool.starmap(the_get.get_web,get_aim_list(i))
    end_t = t.clock()
    thetime = end_t-sta_t
    print('共耗时'+str(thetime)+'秒')
    print('已取得数据' + str(out_queue.qsize()) + '条!')
    db.close()
