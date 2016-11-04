import click
import re
import time
import logging
import sys
import os, os.path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from config import *
from mongo import *
from operator import *


# 41994
class LaLiParser:
    html = ''

    def scrape(self, url):
        webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.Accept-Language'] = 'ru-RU'
        browser = webdriver.PhantomJS()
        browser.get(url)
        self.html = BeautifulSoup(browser.page_source, 'lxml')
        os.system("kill -9 `ps aux | grep phantomjs | awk '{print $2}'`")

    def createUrl(self, args=False):
        result = {
            'url': Config.liveinternetUrl,
        }
        try:
            result['url'] = Config.liveinternetUrl + '#' + ';'.join(['{}={}'.format(key, args[key]) for key in sorted(list(args.keys()))])
            result.update(args)
            return result
        except:
            return result

    def setTasksByGroups(self, groups=[]):
        if groups == 'all':
            groups = []
            for group in Group.objects():
                groups.append(group.alias)

        for group in groups:
            self.walkGroup(group)

    def walkGroup(self, group):
        try:
            args = {'group': group, 'period': 'month', 'geo': 'ru'}
            url = self.createUrl(args)
            group = Group.objects(alias=url['group']).first()

            print ('========== Создаем очередь для категории "{}" =========='.format(group.name))
            self.setTask(url)
            self.scrape(url['url'])
            pages = self.getPaging()
            if pages:
                i = 2
                while i <= pages:
                    args.update({'page': i})
                    url = self.createUrl(args)
                    self.setTask(url)
                    i = i + 1
                print ('{} pages was added'.format(Task.objects(group=group.alias).count()))
            else:
                print ('Ошибка создания очереди для "{}"'.format(group.name))
        except:
            print ('Ошибка обхода группы "{}"'.format(group))
            return False

    def setTask(self, url):
        try:
            Task(url=url['url'], url_dict=url, group=url['group'], timestamp=Config.dateTime).save()
            print ('{} добавлен в очередь'.format(url['url']))
            return True
        except:
            print ('Ошибка сохранения задания')
            return False

    def getItems(self):
        id = 'rows'
        try:
            rows = self.html.find('div', {'id': id})
            if rows:
                result = []
                items = rows.find_all('div', {'class': 'result'})
                for item in items:
                    url = item.find('div', {'class': 'result-link'}).find('div', {'class': 'text'}).find('a').get(
                        'href')
                    name = item.find('div', {'class': 'result-link'}).find('div', {'class': 'text'}).find('a').text

                    result.append({
                        'url': url,
                        'name': name,
                    })

                return result

            else:
                print ('Ошибка. {} не обнаружен'.format(id))
                return False
        except:
            print ('Ошибка сохранения {}'.format(id))
            return False

    def getPaging(self):
        id = 'paging'
        try:
            paging = self.html.find('div', {'id': id})
            if paging:
                result = 0
                for item in paging.findAll('a'):
                    result = int(item.text)
                return result
            else:
                print ('Ошибка. {} не обнаружен'.format(id))
                return False
        except:
            print ('Ошибка сохранения {}'.format(id))
            return False

    def getSelectors(self):
        id = 'selectors'
        try:
            selectors = self.html.find('div', {'id': id})
            if selectors:
                result = {}
                for item in selectors.findAll('a'):
                    name = item.text
                    tuples = re.findall(r'return getRows\(\"(\w+)\", \"(.+)\"\)', item.get('onclick'))
                    for tuple in tuples:
                        if tuple[0] not in result.keys():
                            result.update({tuple[0]: []})
                        result[tuple[0]].append({'alias': tuple[1], 'name': name})
                return result
            else:
                print ('Ошибка. {} не обнаружен'.format(id))
                return False
        except:
            print ('Ошибка сохранения {}'.format(id))
            return False

    def generateListFile(self, items):
        fw = open('list.html', "wt")
        fw.write(
            '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8" />\n<title></title>\n</head>\n<body>\n')
        n = 1
        for i in items:
            fw.write('<a href="{}">{}. {}</a><br>\n'.format(i['link'], n, i['text']))
            n = n + 1
        fw.write('\n</body>\n</html>\n')
        fw.close()

    def generateFile(self, items, file_name='list_' + Config.dateForFile + '.txt', glue=', '):
        try:
            fw = open(file_name, "wt")
            fw.write(glue.join(items))
            fw.close()
            print ('Файл {} успешно сохранен'.format(file_name))
        except:
            print ('Ошибка сохранения файла')

    def saveSite(self, group):
        try:
            groupObj = Group.objects(alias=group).first()
            items = Site.objects(group=groupObj)
            # print (items.url)
            self.generateFile([item.url for item in items if self.filter(item.url)], 'list_' + group + '_' + Config.dateForFile + '.txt')
        except:
            print ('Ошибка подготовки сохранения файла')

    def filter(self, site):
        urlParse = urlparse(site)
        if len(urlParse.path) > 1:
            return False
        return True

    def showGroups(self):
        try:
            for group in Group.objects():
                print ('{} - {}'.format(group.alias, group.name))
        except:
            print ('Ошибка вывода групп')
            return False

    def showSites(self, group):
        try:
            groupObj = Group.objects(alias=group).first()
            if (groupObj):
                for site in Site.objects(group=groupObj):
                    print ('{} - {}'.format(site.url, site.name))
            else:
                print ('Group "{}" was not found'.format(group))
        except:
            print ('Ошибка вывода сайтов')
            return False

    def showCount(self, object):
        try:
            objectCount = globals()[object].objects().count()
            if (objectCount):
                print ('Count of {} - {}'.format(object, objectCount))
            else:
                print ('Object "{}" was not found'.format(object))
        except:
            print ('Ошибка вывода количества объектов')
            return False

    def goTask(self):
        try:
            task = Task.objects().first()
            if (task):
                print (task.url)
                time.sleep(10)
                self.scrape(task['url'])
                task.delete()
                self.saveSites(task['url_dict'])
                self.goTask()
            else:
                print ('Список заданий пуст')

        except:
            print ('Ошибка обхода списка')
            return False

    def missingToTask(self):
        try:
            missing = Missing.objects()
            if missing:
                print ('Found {} missing urls'.format(missing.count()))
                for missing_url in missing:
                    self.setTask(missing_url.url)
                    missing_url.delete()
                if missing.count() == 0:
                    print ('All missing urls are tasked')
                    print ('Found {} tasks'.format(Task.objects().count()))
            else:
                print ('Список missing пуст')

        except:
            print ('Ошибка переноса списка из missing в task')
            return False

    def walkGroups(self, groups=[]):
        try:
            if groups == 'all':
                groups = []
                for group in Group.objects():
                    groups.append(group.alias)

            for group in groups:
                self.walkGroup(group)

        except:
            print ('Ошибка обхода групп')
            return False

    def saveSites(self, url):
        try:
            items = self.getItems()
            if (items):
                for item in items:
                    try:
                        group = Group.objects(alias=url['group']).first()
                        if (group):
                            Site(url=item['url'], name=item['name'], group=group, timestamp=Config.dateTime).save()
                            print ('Site "{}" was saved'.format(item['name']))
                        else:
                            print ('Group "{}" was not found'.format(url['group']))
                    except:
                        print ('Site "{}" is already created'.format(item['name']))

            else:
                print ('Ошибка. "Items" не найден')
                self.saveMissing(url)
                self.setTask(url)
                return False
        except:
            print ('Ошибка сохранения "Items"')
            return False

    def saveSelectors(self):
        try:
            self.scrape(Config.liveinternetUrl)
            selectors = self.getSelectors()
            if (selectors):
                for group in selectors['group']:
                    try:
                        Group(alias=group['alias'], name=group['name']).save()
                        print ('Group "{}" was saved'.format(group['name']))
                    except:
                        print ('Group "{}" is already created'.format(group['name']))
                print ('Found {} groups'.format(Group.objects().count()))

            else:
                print ('Ошибка. "Selectors" не найден')
                return False
        except:
            print ('Ошибка сохранения "Selectors"')
            return False

    def saveMissing(self, url):
        try:
            Missing(url=url).save()
            print ('Missing url "{}" was saved'.format(url['url']))
        except:
            print ('Ошибка сохранения "Missing url"')
            return False

    def dbDrop(self):
        mongo.drop_database(db)
        try:
            mongo.drop_database(db)
            print ('Db удалена')
            return True
        except:
            print ('Ошибка удаления Db')
            return False

    def dbRestore(self):
        self.dbDrop()
        fileDict = [{'name': file, 'time': os.path.getmtime(Config.backupsDir + file)} for file in os.listdir(Config.backupsDir)]
        fileDict = sorted(fileDict, key=itemgetter('time'), reverse=True)
        newestDump = Config.backupsDir + fileDict[0]['name']
        code = os.system(Config.mongodbConfig['commands']['restore'].format(db, newestDump))
        if code == 0:
            print ('Db восстановлена')
        else:
            print ('Ошибка восстановления БД')

    def dbDump(self):
        if not os.path.exists(Config.backupsDir):
            print('Create folder ' + Config.backupsDir)
            os.makedirs(Config.backupsDir)
        backupName = Config.mongodbConfig['backup_name']
        code = os.system(Config.mongodbConfig['commands']['dump'].format(db, backupName))
        if code == 0:
            print ('Резервная копия Db создана')
        else:
            print ('Ошибка создания резервной копии БД')


LaLiParser = LaLiParser()


@click.group()
@click.version_option(version=Config.progVersion, prog_name=Config.progName, message='%(prog)s %(version)s')
def cli():
    """LaCodda LiveInternet Parser (LaLiParser).
    Grab Tool.
    """


@cli.group('grab')
def grab():
    """Grab Tool."""


@grab.command('selectors')
def grab_selectors():
    """Grab selectors"""
    LaLiParser.saveSelectors()


@grab.command('group')
@click.argument('group', default='house')
@click.option('--period', default='month', help='')
@click.option('--geo', default='ru', help='')
def grab_group(group):
    """Grab group"""
    LaLiParser.walkGroup(group)


@grab.command('groups')
@click.argument('groups', default=['job', 'meeting', 'games', 'rest', 'humor'])
def grab_groups(groups):
    """Grab groups"""
    LaLiParser.saveSelectors()
    LaLiParser.walkGroups(groups)


@cli.group('task')
def task():
    """Grab Tool."""


@task.command('set')
@click.argument('groups', default=['job', 'meeting', 'games', 'rest', 'humor'])
def task_set(groups):
    """Set tasks"""
    LaLiParser.saveSelectors()
    LaLiParser.setTasksByGroups(groups)


@task.command('go')
def task_go():
    """Go Tasks"""
    LaLiParser.goTask()


@task.command('missing')
def task_missing():
    """Missing to Tasks"""
    LaLiParser.missingToTask()


@cli.group('show')
def show():
    """Show Tool."""


@show.command('url')
def show_url():
    """Show URL"""
    args = {'group': 'group', 'period': 'month', 'geo': 'ru'}
    print (LaLiParser.createUrl(args))


@show.command('groups')
def show_groups():
    """Show groups"""
    LaLiParser.showGroups()


@show.command('sites')
@click.argument('group', default='house')
def show_sites(group):
    """Show sites"""
    LaLiParser.showSites(group)


@show.command('count')
@click.argument('object', default='Site')
def show_count(object):
    """Show count of any object"""
    LaLiParser.showCount(object)


@cli.group('save')
def save():
    """Save Sites."""


@save.command('site')
@click.argument('group', default='job')
def save_site(group):
    """Save site to file"""
    LaLiParser.saveSite(group)


@cli.group('database')
def database():
    """Database Tool."""


@database.command('drop')
def database_drop():
    """Drop database"""
    LaLiParser.dbDrop()


@database.command('restore')
def database_restore():
    """Restore database"""
    LaLiParser.dbRestore()


@database.command('dump')
def database_dump():
    """Dump database"""
    LaLiParser.dbDump()


if __name__ == '__main__':
    cli()
