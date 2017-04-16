'''
需求：编写一个爬虫，要求能提供一个有效IP的列表，并能自动更新这个列表以获取有效性
思路：
1.编写一个函数，先从网站中获取所有IP地址，并利用集合去重后形成一个IP待筛选列表
2.编写一个多线程的类，能够查验上述列表中的有效性，并将通过筛选的有效IP放入另一个有效IP列表
3.编写一个函数output_ip,封装上述两个功能，函数的参数设置为多线程类的线程数
'''
import re
import urllib.request
import time as t
from bs4 import BeautifulSoup
import threading
import queue

Ip_par = '(?:(?:1\d\d|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.){3}(?:1\d\d|2[0-4]\d|25[0-5]|[1-9]\d|\d)\:\d+'
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

#定义一个获取IP免费网站网址的列表
Web_Info = [ 'http://www.youdaili.net/Daili/http/']

# 定义一个队列作为容器
workqueue = queue.Queue()

#定义一个类
class Ip_getfirst:
    Ip_par = Ip_par
    headers = headers
    def __init__(self,info,workqueue):
        self.web_index = info
        self.url_num = ''
        self.workqueue = workqueue
    #定义一个函数，获取最新IP代理的URL页面
    def Get_last_index(self,url):
        Code_body = urllib.request.Request(url, headers=self.headers)
        Code_body = urllib.request.urlopen(Code_body).read().decode('utf-8')
        soup = BeautifulSoup(Code_body,'lxml')
        soup_body = soup.select('div.chunlist > ul > li > p > a')
        print('正在获取'+soup_body[0].get_text())
        self.url_num = soup_body[0].get('href').split('/')[-1].split('.')[0]
        return soup_body[0].get('href')

    #定义一个函数，从单个网页上所有IP
    def Get_ip_f(self,url):
        Code_body = urllib.request.Request(url,headers = self.headers)
        Code_body = urllib.request.urlopen(Code_body).read().decode('utf-8')
        Ip_from_web = re.findall(self.Ip_par,Code_body)
        #print(Ip_from_web)
        return Ip_from_web

    #在上面函数基础上，从连续的网页获取所有IP
    def Get_ip(self,url):
        IP_url = self.Get_last_index(url)
        Ip_All = self.Get_ip_f(IP_url)
        i = 1
        while True:
            i += 1
            url = IP_url.replace(self.url_num, self.url_num + '_' + str(i))
            try:
                Code_body = urllib.request.Request(url, headers=self.headers)
                Code_body = urllib.request.urlopen(Code_body,timeout=3).read().decode('utf-8')
                soup = BeautifulSoup(Code_body, 'lxml')
            except Exception as e:
                if e.code == 404:
                    break
            Ip_All += self.Get_ip_f(url)
        print('共获取 %d 个IP' % len(Ip_All))
        return Ip_All
    #依次从取出免费IP网站的URL，采集其IP
    def get_ip_url(self):
        # 定义一个储存IP的列表
        Ip_Info = []
        for i in self.web_index:
            Ip_Info += self.Get_ip(i)
        #利用集合去除重复的
        Ip_Info = set(Ip_Info)
        print('去重后得到 %d 个,已全写入队列中' % len(Ip_Info))
        return Ip_Info

class Ip_getting(threading.Thread):
    headers = headers
    def __init__(self,workqueue,Ip_pass,name):
        super().__init__()
        self.workqueue = workqueue
        self.Ip_pass = Ip_pass
        self.name = name
    #定义一个函数，验证IP是否有效
    def Verify_ip(self,ip):
        proxy_support = urllib.request.ProxyHandler({'http':str(ip)})
        opener = urllib.request.build_opener(proxy_support)
        opener.addheaders = [('User-Agent',self.headers['User-Agent'])]
        urllib.request.install_opener(opener)
        try:
            Web_body = urllib.request.urlopen('http://www.whatismyip.com.tw/',timeout=1).read().decode('utf-8')
            Ip_pa = '(?:(?:1\d\d|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.){3}(?:1\d\d|2[0-4]\d|25[0-5]|[1-9]\d|\d)(?:\:\d+){0,1}'
            Ip_from_web = re.findall(Ip_pa, Web_body)
            if Ip_from_web:
                if Ip_from_web[0] == str(ip).split(':')[0]:
                    #print('“IP获取者”的线程%s已获得有效IP%s' % (self.name,ip))
                    return ip
        except Exception as e:
            pass
    #定义一个函数，封装所有的任务
    def run(self):
        print('“IP获取者”的线程%s已启动' % self.name)
        while True:
            ip = self.workqueue.get()
            if self.Verify_ip(ip):
                self.Ip_pass.append(ip)
            if workqueue.qsize() == 0:
                # print('队列中的ip全部处理完毕，准备进入下一个任务...')
                break

print('开始生成IP代理池...')
Ip_get = Ip_getfirst(Web_Info, workqueue)
ip_list = Ip_get.get_ip_url()

#将上述函数封装到一个多线程类中，以方便其他模块调用其进行并发使用
class IP_GET(threading.Thread):
    def __init__(self,IP_pass,num = 1,sep_time = 0):
        super().__init__()
        self.IP_pass = IP_pass
        self.inter_list = []#中间容器
        self.num = num
        self.sep_time = sep_time#筛选IP的间隔时间

    def output_ip(self,t_list):
        del t_list[:]
        for each in ip_list:
            workqueue.put(each)

        start = t.clock()
        for i in range(1, self.num + 1):
            ip_thread_a = Ip_getting(workqueue,t_list, str(i))
            ip_thread_a.daemon = True
            ip_thread_a.start()

        # 每十秒显示一下待筛选队列里的剩余的未被筛选IP数量，当数量为零时表示队列中IP都被筛选完毕，返回这个列表
        while True:
            t.sleep(10)
            # print('目前队列中共有 %d 个ip' % workqueue.qsize())
            if workqueue.qsize() == 0:
                # print('队列中的ip全部处理完毕，准备进入下一个任务...')
                break
        # workqueue.join()
        end = t.clock()
        print('本次更新代理池共用时%.3f秒...' % (end - start))
        #return IP_pass
    def run(self):
        while True:
            if len(self.IP_pass) <= 5:
                print('IP池中数量不足，开始更新')
                self.output_ip(self.inter_list)
                del self.IP_pass[:]
                self.IP_pass.extend(self.inter_list)
                print('代理池中共有 %d 个有效代理IP可以正常使用，分别是' % len(self.IP_pass))
                print(self.IP_pass)
                t.sleep(self.sep_time)#设置时间间隔
                print('正在运行的线程有' + str(threading.enumerate()) + '共' + str(len(threading.enumerate())) + '个')
            t.sleep(15)

if __name__ == '__main__':
    alist = ['122.224.226.187:8080']
    a = IP_GET(alist,num = 40)
    a.start()





