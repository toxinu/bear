# -*- coding: utf-8 -*-
import logging
from .base import BasePlugin

logger = logging.getLogger('plugins.guesser')


class GuesserPlugin(BasePlugin):
    def pre_add_feed(self, url):
        return url
