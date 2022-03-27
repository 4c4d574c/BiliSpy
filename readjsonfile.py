#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import queue
import time
import re


class JsonPart(object):
    def __init__(self, flname):
        self.maxsize = 32
        self.jspart = list()
        self.fl = open(flname, "r", encoding="utf8")
        self.partqueue = queue.Queue()
        self.leftcount = 0
        # self.partlist = list()
        self.flend = 0
        self.eof = False
        # self.stack = list()
        self.getFileEnd()
        self.starttime = 0
        self.readtime = 0
        self.tran = False
        self.strstart = False
        self.flags = set(["\"", "\\", "{", "}"])
        # self.flags = ["\\", "}", "\"", "{"]
    
    def getFileEnd(self):
        self.fl.seek(0, 2)
        self.flend = self.fl.tell()
        self.fl.seek(0, 0)
    
    def test1(self, block):
        for c in block:
            if ((self.strstart == False) and (c == "{")):
                self.leftcount += 1
            elif ((self.strstart == False) and (c == "}")):
                self.leftcount -= 1
                if ((self.leftcount == 0) and (self.jspart != [])):
                    self.jspart.append(c)
                    self.jspart = ["".join(self.jspart)]
                    self.partqueue.put(self.jspart[0])
                    self.starttime = time.time()
                    self.jspart = []
            elif ((self.tran == False) and (c == "\"")):
                self.strstart = (not self.strstart)
            elif ((self.tran == True) and (c == "\"")):
                self.tran = False
            elif (c == "\\"):
                self.tran = True
            else:
                if (self.tran == True):
                    self.tran = False
            if (self.leftcount > 0):
                self.jspart.append(c)
    
    def test2(self, block):
        for c in block:
            # if ((self.strstart == True) and (c not in ["\"", "\\", "{", "}"])):
            if ((self.strstart == True) and (c not in self.flags)):
                if (self.tran == True):
                    self.tran = False
            elif ((self.tran == False) and (c == "\"")):
                self.strstart = (not self.strstart)
            elif ((self.tran == True) and (c == "\"")):
                self.tran = False
            elif ((self.strstart == False) and (c == "{")):
                self.leftcount += 1
            elif ((self.strstart == False) and (c == "}")):
                self.leftcount -= 1
                if ((self.leftcount == 0) and (self.jspart != [])):
                    self.jspart.append(c)
                    self.partqueue.put("".join(self.jspart))
                    self.jspart = []
            elif (c == "\\"):
                self.tran = True
            else:
                pass
            if (self.leftcount > 0):
                self.jspart.append(c)

    def addPart(self):
        while ((self.partqueue.qsize() < self.maxsize) and (not self.eof)):
            if (self.fl.tell() != self.flend):
                block = self.fl.read(1024*20)
            else:
                self.eof = True
                break
            self.test2(block)
            # for c in block:
            #     if ((self.strstart == True) and (c not in ["\"", "\\", "{", "}"])):
            #         if (self.tran == True):
            #             self.tran = False
            #     elif (c == "\\"):
            #         self.tran = True
            #     elif ((self.tran == False) and (c == "\"")):
            #         self.strstart = (not self.strstart)
            #     elif ((self.tran == True) and (c == "\"")):
            #         self.tran = False
            #     elif ((self.strstart == False) and (c == "{")):
            #         self.leftcount += 1
            #     elif ((self.strstart == False) and (c == "}")):
            #         self.leftcount -= 1
            #         if ((self.leftcount == 0) and (self.jspart != [])):
            #             self.jspart.append(c)
            #             self.partqueue.put("".join(self.jspart))
            #             self.jspart = []
            #     else:
            #         pass
            #         # if (self.tran == True):
            #         #     self.tran = False
            #     if (self.leftcount > 0):
            #         self.jspart.append(c)
            # for c in block:
            #     if ((self.strstart == False) and (c == "{")):
            #         self.leftcount += 1
            #     elif ((self.strstart == False) and (c == "}")):
            #         self.leftcount -= 1
            #         if ((self.leftcount == 0) and (self.jspart != "")):
            #             self.jspart.append(c)
            #             self.jspart = ["".join(self.jspart)]
            #             self.partqueue.put(self.jspart[0])
            #             self.starttime = time.time()
            #             self.jspart = []
            #     elif ((self.tran == False) and (c == "\"")):
            #         self.strstart = (not self.strstart)
            #     elif ((self.tran == True) and (c == "\"")):
            #         self.tran = False
            #     elif (c == "\\"):
            #         self.tran = True
            #     else:
            #         if (self.tran == True):
            #             self.tran = False
            #     if (self.leftcount > 0):
            #         self.jspart.append(c)
        # print("queue size: {}".format(self.partqueue.qsize()))
    
    def getOne(self):
        while (self.partqueue.empty() and (not self.eof)):
            start = time.time()
            self.addPart()
            print("add a part time: {}".format(time.time()-start))
        if (not self.partqueue.empty()):
            return self.partqueue.get()
        else:
            return None



def jsoniterator(flname):
    stack = []
    jspart = ""
    with open(flname, "r") as fl:
        while (True):
            c = fl.read(1)
            if (c == ""):
                break
            jspart += c
            if (c == "{"):
                stack.append(c)
            elif (c == "}"):
                stack.pop()
                if (stack == [] and (jspart != "")):
                    yield jspart
                    jspart = ""
            else:
                pass

def printJ(jspart: JsonPart):
    count = 0
    part = jspart.getOne()
    while (part != None):
        try:
            json.loads(part)
        except Exception as e:
            print(part)
            # with open("fail.json", "a") as fl:
            #     fl.write(part)
        count += 1
        part = jspart.getOne()
    print(count)


def readALL(flname):
    count = 0;
    partlist = list()
    with open(flname, "r") as fl:
        line = fl.readline()
        while (line != ""):
            partlist.append(line)
            if (line.rstrip() == "}"):
                part = "".join(partlist)
                count += 1
                partlist.clear()
            line = fl.readline()
        print(count)



if __name__ == "__main__":
    # readALL("crgg.json")
    # jspart = JsonPart("供地计划.json")
    # jspart = JsonPart("fail.json")
    # start = time.time()
    # printJ(jspart)
    # print("用时：{}".format(time.time()-start))
    # print(jspart.eof)
