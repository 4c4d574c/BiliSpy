#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import uuid
import requests
import random
import queue
import calendar
from allcon import MAX_WORKER, HEADER, URL_BASE_TIME
from bilibilifield import ALLFIELD
from MyProxy import Proxies
from concurrent.futures import ThreadPoolExecutor as TP
from concurrent.futures import as_completed


class BiliBili(object):
    def __init__(self, flname, field, type):
        self.flname = flname
        self.field = field
        self.type = type
        self.referer = ""
        self.proxy = Proxies()
        self.session = requests.Session()
        self.pagefalied = queue.Queue()
        self.monthfailed = queue.Queue()
        self.jsonqueue = queue.Queue()
        self.respqueue = queue.Queue()

    def setHeader(self):
        url = ALLFIELD[self.field]["referer"] + ALLFIELD[self.field]["types"][self.type]["url"]
        HEADER["referer"] = url
    
    def dateRange(self, year, month):
        monthrange = []
        cal = calendar.Calendar()
        for date in cal.itermonthdates(year, month):
            if (date.month == month):
                monthrange.append(date)
        
        return {"startdate": monthrange[0].strftime("%Y%m%d"), "endtime": monthrange[-1].strftime("%Y%m%d")}
    
    def parseJson(self, resp_content: str)->dict:
        js = re.search("{.*}", resp_content)
        if (js != None):
            try:
                jsobj = json.loads(js.group())
            except Exception as e:
                print("parseJson exceptions: {}".format(e))
            else:
                    return jsobj
        else:
            print("parseJson: No match string!")
            return None
    
    def getResp(self, url: str)->requests.Response:
        max_try = 5
        while (max_try):
            proxies = self.proxy.getProxy()
            try:
                resp = self.session.get(url, headers=HEADER, proxies=proxies, timeout=20)
            except Exception as e:
                print("getResp exceptions: {}".format(e))
                max_try -= 1
                continue
            else:
                if (resp.status_code != 200):
                    max_try -= 1
                    continue
            break
        if (max_try <= 0):
            print("getResp failed!")
            return None
        else:
            return resp
    
    def getTotalpage(self, starttime, endtime)->int:
        max_try = 5
        while (max_try):
            resp = self.getResp(URL_BASE_TIME.format(ALLFIELD[self.field]["types"][self.type]["cate_id"], 1, starttime, endtime, str(random.random())[2:]))
            if (resp == None):
                max_try -= 1
                continue
            data = self.parseJson(resp.content.decode())
            if (data == None):
                max_try -= 1
                continue
            if ("numPages" in data.keys()):
                return int(data["numPages"])
            else:
                max_try -= 1
        print("getTotalpage failed")
        return -1

    def setCookie(self):
        max_try = 5
        while (max_try):
            resp = self.getResp(HEADER["referer"])
            if (resp == None):
                max_try -= 1
                continue
            break
        if (max_try <= 0):
            raise Exception("setCookie failed!")
        cookiejar = self.session.cookies
        cookiejar.set("b_lsid", "4C67AD83_17E04FF56E5", domain=".bilibili.com")
        cookiejar.set("_uuid", "{}infoc".format(uuid.uuid1().hex), domain=".bilibili.com")
    
    def downloadFailedMonth(self):
        while (not self.monthfailed.empty()):
            year, month = self.monthfailed.get()
            self.getOneMonthPages(year, month)

    def downloadFailedPage(self, starttime, endtime, successflname):
        while (not self.pagefalied.empty()):
            pagenum = self.pagefalied.get()
            page = self.getPageResp(pagenum, starttime, endtime)
            if (page != None):
                self.writeFile(page, self.flname)
                self.writeSuccess(pagenum, successflname)
                print("失败页面{}已完成下载！".format(pagenum))
    
    def getPageResp(self, pagenum, starttime, endtime)->list:
        max_try = 5
        url = URL_BASE_TIME.format(ALLFIELD[self.field]["types"][self.type]["cate_id"], pagenum, starttime, endtime, str(random.random())[2:])
        while (max_try):
            try:
                resp = self.getResp(url)
            except Exception as e:
                print("getPage exceptions: {}".format(e))
                max_try -= 1
            else:
                if (resp == None):
                    max_try -= 1
                else:
                    resp_obj = self.parseJson(resp.content.decode())
                    if (resp_obj != None and "result" in resp_obj.keys()):
                        return resp_obj["result"]
                    else:
                        max_try -= 1
                        continue
        if (max_try <= 0):
            self.pagefalied.put(pagenum)
            print("第{}页请求失败，已加入到失败队列！".format(pagenum))
            return None
    
    def writeFile(self, data, flname):
        with open(flname, "a") as fl:
            fl.write(json.dumps(data, ensure_ascii=False, indent=4) + "\n")
    
    def writeSuccess(self, pagenum, flname):
        with open(flname, "a+") as fl:
            fl.write(str(pagenum) + "\n")
    
    def ignorePageNum(self, flname)->list:
        successcode = list()
        if (os.path.exists(flname)):
            with open(flname, "r") as fl:
                for ele in fl.readlines():
                    successcode.append(ele.strip())
        
        return successcode
    
    def getAllPage(self, starttime, endtime, totalpage, successflname):
        pagenums = []
        successcode = self.ignorePageNum(successflname)
        with TP(max_workers=MAX_WORKER) as executor:
            for i in range(1, totalpage+1):
                if (str(i) not in successcode):
                    pagenums.append(i)
            alldata = {executor.submit(self.getPageResp, page, starttime, endtime): page for page in pagenums}
            for data in as_completed(alldata):
                pagenum = alldata[data]
                try:
                    result = data.result()
                except Exception as e:
                    print("getAllPage exceptions: {}".format(e))
                else:
                    if (result != None):
                        del alldata[data]
                        print("{}-{}的第{}页请求完成!".format(starttime, endtime, pagenum))
                        for ele in result:
                            self.writeFile(ele, self.flname)
                        self.writeSuccess(pagenum, successflname)
    
    def getOneMonthPages(self, year, month):
        max_try = 5
        starttime, endtime = self.dateRange(year, month).values()
        while (max_try):
            totalpage = self.getTotalpage(starttime, endtime)
            if (totalpage < 0):
                max_try -= 1
                totalpage = 0
            else:
                break
        if (max_try <= 0):
            self.monthfailed.put([year, month])
            print("{}年{}月请求失败，已添加到失败队列！".format(year, month))
        self.getAllPage(starttime, endtime, totalpage, str(year)+str(month)+"_success.txt")
        print("开始下载失败页面。")
        self.downloadFailedPage(starttime, endtime, str(year)+str(month)+"_success.txt")
    
    def downloadAllMonth(self, startyear, endyear, startmonth, endmonth):
        tmpname = self.flname
        for year in range(startyear, endyear+1):
            self.flname = "{}_{}".format(year, tmpname)
            for month in range(startmonth, endmonth+1):
                self.getOneMonthPages(year, month)
    
    def start(self, startyear, endyear, startmonth, endmonth):
        self.setHeader()
        self.setCookie()
        self.downloadAllMonth(startyear, endyear, startmonth, endmonth)
        print("开始下载失败月份。")
        self.downloadFailedMonth()


if __name__ == "__main__":
    b = BiliBili("电子竞技_bilibili.json", "游戏", "电子竞技")
    b.start(2009, 2009, 6, 12)
