# -*- coding: utf-8 -*-
from .base import BasePlugin


class GuesserPlugin(BasePlugin):
    def pre_add_feed(self, url):
        return url
