# -*- coding: utf-8 -*-


class BasePlugin:
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
