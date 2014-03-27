# -*- coding: utf-8 -*-
"""
Description
===========
This is BasePlugin description.

Install
=======
pip install deps

Example
=======
[plugin:baseplugin]
settings_1 = True
settings_2 = test
"""


class BasePlugin:
    def __init__(self, **kwargs):
        self.config = kwargs

    def dependencies(self):
        pass

    def pre_add_feed(self, url):
        raise NotImplementedError

    def post_add_feed(self, feed):
        raise NotImplementedError

    def pre_delete_feed(self, feed):
        raise NotImplementedError

    def post_delete_feed(self, feed):
        raise NotImplementedError

    def pre_reset_feed(self, feed):
        raise NotImplementedError

    def post_reset_feed(self, feed):
        raise NotImplementedError

    def post_set_feed(self, feed):
        raise NotImplementedError

    def pre_send_email(self, sender, to, subject, message, feed, entry):
        raise NotImplementedError
