# -*- coding: utf-8 -*-
"""
Description
===========
This plugin will try to guess if you give feed url or website url.
If website url is given, it will try to guess feed url.

Install
=======
Nothing.

Example
=======
Nothing.
"""
import logging
from .base import BasePlugin

logger = logging.getLogger('plugins.guesser')


class GuesserPlugin(BasePlugin):
    pass
