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
from urllib.parse import urlparse
from urllib.parse import urlunsplit


class Linker:
    DATE = time.strftime('%Y-%m-%d_%H-%M-%S')

    HOSTLIST = []

    LINKLIST = []

    FINISHEDLINKLIST = {}

    GRABCOUNT = 0

    def recursGrab(self):
        for url in self.LINKLIST:

            grabbedPage = self.grabLinks(url)
            logging.info(self.filterList(grabbedPage))
            print (self.filterList(grabbedPage))
            if isinstance(grabbedPage, list):
                grabLinkList = self.filterList(self.delDouble(grabbedPage))
                grabCount = len(grabLinkList)
                if grabCount > 0:
                    self.addLinkList(grabLinkList)
            if isinstance(grabbedPage, bool) and grabbedPage == False:
                self.FINISHEDLINKLIST.update({url: 'ERROR'})
            self.LINKLIST.remove(url)

        if len(self.LINKLIST) > 0:
            self.recursGrab()

    def grabLinks(self, url):
        grabLinkList = list()
        g = Grab()
        print (url)
        logging.info(url)
        try:
            g.setup(timeout=30, connect_timeout=40)
            g.go(url)
            print (g.response.code)
            logging.info(g.response.code)
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
        except:
            return False

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

    def generateListFile(pageMap):
        fw = open('list.html', "wt")
        fw.write(
            '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8" />\n<title></title>\n</head>\n<body>\n')
        n = 1
        for i in pageMap:
            fw.write('<a href="%s">%s. %s</a><br>\n' % (i, n, i))
            n = n + 1
        # end for
        fw.write('\n</body>\n</html>\n')
        fw.close()

    def getHost(self, site):
        urlParse = urlparse(site)
        if urlParse.scheme == '':
            return 'Error. Please, type protocol (http, https, etc)'

        self.HOSTLIST.append(urlunsplit([urlParse.scheme, urlParse.netloc, '', '', '']))
        if 'www.' not in urlParse.netloc[:4]:
            self.HOSTLIST.append(urlunsplit([urlParse.scheme, 'www.' + urlParse.netloc, '', '', '']))
        else:
            self.HOSTLIST.append(urlunsplit([urlParse.scheme, urlParse.netloc[4:], '', '', '']))
        self.HOSTLIST.append(urlParse.netloc.replace(".", "_"))
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
                logging.basicConfig(filename=self.HOSTLIST[2] + '_' + self.DATE + '.log', level=logging.INFO)
                logging.info('Started')
                print (self.HOSTLIST)
                self.LINKLIST.append(self.HOSTLIST[0])
                self.recursGrab()
                self.FINISHEDLINKLIST = OrderedDict(
                    sorted(self.FINISHEDLINKLIST.items(), key=lambda x: x[0], reverse=False))
                self.FINISHEDLINKLIST = OrderedDict(
                    sorted(self.FINISHEDLINKLIST.items(), key=lambda x: x[1], reverse=False))
                # print sorted(self.FINISHEDLINKLIST.items(), key=lambda (k, v): v, reverse=True)
                count = len(self.FINISHEDLINKLIST)
                for (link, code) in self.FINISHEDLINKLIST.items():
                    print ('{} - {}'.format(code, link.encode('utf-8')))
                print ('Ссылок найдено: %d' % count)
                logging.info('Finished')
            else:
                print (host)


if __name__ == '__main__':
    obj = Linker()
    obj.main()
