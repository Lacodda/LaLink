from mongoengine import *
from pymongo import MongoClient
from config import *
import os

db = Config.mongodbConfig['database']

mongo = MongoClient(Config.mongodbConfig['host'], Config.mongodbConfig['port'])
# print (mongo.database_names())

connect(db)


class Period(Document):
    alias = StringField(required=True, unique=True)
    name = StringField(max_length=250, required=True)


class Geo(Document):
    alias = StringField(required=True, unique=True)
    name = StringField(max_length=250, required=True)


class Group(Document):
    alias = StringField(required=True, unique=True)
    name = StringField(max_length=250, required=True)


class Language(Document):
    alias = StringField(required=True, unique=True)
    name = StringField(max_length=250, required=True)


class Revision(Document):
    started_at = DateTimeField()
    finished_at = DateTimeField()
    new_items = IntField()
    total_items = IntField()
    group = ListField(ReferenceField(Group))


class Site(Document):
    url = StringField(required=True, unique=True)
    name = StringField(max_length=250, required=True)
    group = ReferenceField(Group)
    revision = ListField(ReferenceField(Revision))
    timestamp = DateTimeField(required=True)


class Missing(Document):
    url = DictField(required=True, unique=True)


class Task(Document):
    url = StringField(required=True, unique=True)
    url_dict = DictField(required=True)
    group = StringField(required=True)
    timestamp = DateTimeField(required=True)
