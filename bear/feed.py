# -*- coding: utf-8 -*-
from datetime import datetime
from peewee import Model
from peewee import CharField
from peewee import DateTimeField

from .core import DB


class Feed(Model):
    url = CharField(unique=True)
    added = DateTimeField(default=datetime.now)
    updated = DateTimeField(null=True)

    class Meta:
        database = DB
