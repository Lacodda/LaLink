#!/usr/bin/env python
# -*- coding: utf-8 -*-
import gzip
import os
from collections import OrderedDict
import time
import sys
import argparse
from grab import Grab
import logging
import tarfile
from ftplib import FTP
from urlparse import urlparse
from urlparse import urlunsplit

class Linker:

    HOSTLIST = []

    LINKLIST = []

    FINISHEDLINKLIST = {}

    GRABCOUNT = 0


    def recursGrab(self):
        for url in self.LINKLIST:

            grabbedPage = self.grabLinks(url)
            if isinstance(grabbedPage, list):
                grabLinkList = self.filterList(self.delDouble(grabbedPage))
                grabCount = len(grabLinkList)
                if grabCount > 0:
                    self.addLinkList(grabLinkList)
            self.LINKLIST.remove(url)

        if len(self.LINKLIST) > 0:
            self.recursGrab()


    def grabLinks(self, url):
        grabLinkList = list()
        g = Grab()
        g.go(url)
        self.FINISHEDLINKLIST.update({url: g.response.code})
        if g.response.code == 200:
            links = g.doc.select('//*[@href]')
            for link in links:
                grabLinkList.append(link.attr('href'))
            return grabLinkList
        if g.response.code == 404:
            return '404 Found'
        else:
            return 'Error connect'


    def delDouble(self, linkList):
        uniqueLinkList = list()
        for link in linkList:
            if link not in uniqueLinkList and '#' not in link[:1] and link != '/':
                uniqueLinkList.append(link)
            else:
                continue
        return uniqueLinkList


    def addLinkList(self, linkList):
        for link in linkList:
            if link not in self.LINKLIST and link not in self.FINISHEDLINKLIST.keys():
                self.LINKLIST.append(link)
            else:
                continue


    def filterList(self, linkList):
        filteredList = list()
        pageExt = ['.htm', '.html', '.php', '.br', '.asp', '.py']
        for link in linkList:
            urlParse = urlparse(link)
            if urlParse.scheme == '':
                hostParse = urlparse(self.HOSTLIST[0])
                link = urlunsplit([hostParse.scheme, hostParse.netloc, link, '', ''])
                urlParse = urlparse(link)

            if urlunsplit([urlParse.scheme, urlParse.netloc, '', '', '']) not in self.HOSTLIST:
                continue

            if urlParse.fragment != '':
                continue

            filename, ext = os.path.splitext(urlParse.path)

            if ext != '' and ext not in pageExt:
                continue

            filteredList.append(link)

        return filteredList


    def getHost(self, site):
        urlParse = urlparse(site)
        if urlParse.scheme == '':
            return 'Error. Please, type protocol (http, https, etc)'

        self.HOSTLIST.append(urlunsplit([urlParse.scheme, urlParse.netloc, '', '', '']))
        if 'www.' not in urlParse.netloc[:4]:
            self.HOSTLIST.append(urlunsplit([urlParse.scheme, 'www.' + urlParse.netloc, '', '', '']))
        else:
            self.HOSTLIST.append(urlunsplit([urlParse.scheme, urlParse.netloc[4:], '', '', '']))

        return True


    def createParser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', '--site', default='')

        return parser


    def main(self):
        parser = self.createParser()
        namespace = parser.parse_args(sys.argv[1:])
        if namespace.site == '':
            print ('Введите URL сайта: -s http://www.site.com')
        else:
            print (
                'Привет, сейчас LaLinker соберет все внутренние ссылки с сайта {}. Сбор может занять продолжительное время.'.format(
                    namespace.site))
            host = self.getHost(namespace.site)
            if isinstance(host, bool) and host == True:

                print (self.HOSTLIST)
                self.LINKLIST.append(self.HOSTLIST[0])
                self.recursGrab()
                self.FINISHEDLINKLIST = OrderedDict(sorted(self.FINISHEDLINKLIST.items(), key=lambda x: x[0], reverse=False))
                self.FINISHEDLINKLIST = OrderedDict(sorted(self.FINISHEDLINKLIST.items(), key=lambda x: x[1], reverse=False))
                # print sorted(self.FINISHEDLINKLIST.items(), key=lambda (k, v): v, reverse=True)
                count = len(self.FINISHEDLINKLIST)
                for (link, code) in self.FINISHEDLINKLIST.items():
                    print ('{} - {}'.format(code, link))
                print ('Ссылок найдено: %d' % count)
            else:
                print (host)


if __name__ == '__main__':
    obj = Linker()
    obj.main()
