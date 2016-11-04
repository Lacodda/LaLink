import sys
import time


class Config:
    progAuthor = 'LaCodda'

    progName = 'LaCodda LiveInternet Parser (LaLiParser)'

    progVersion = '0.0.1'

    dateForFile = time.strftime('%Y-%m-%d_%H-%M-%S')

    dateTime = time.strftime('%Y.%m.%d %H:%M:%S')

    liveinternetUrl = 'http://www.liveinternet.ru/rating/'

    backupsDir = sys.path[0] + '/backups/'

    mysqlConfig = {
        'host': 'localhost',
        'user': 'root',
        'password': '1111',
        'commands': {
            'show_databases': 'mysql -u {} -p{} -h {} --silent -N -e "show databases"',
            'dump': 'mysqldump -u {} -p{} {} > {}'
        }
    }

    mongodbConfig = {
        'host': 'localhost',
        'port': 27017,
        'database': 'lalibase',
        'backup_name': backupsDir + 'lalibase_' + dateForFile + '.gz',
        'commands': {
            'restore': 'mongorestore --db {} --archive={} --gzip',
            'dump': 'mongodump --db {} --archive={} --gzip',
        }
    }
