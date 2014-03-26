#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest
from tempfile import mkstemp
from bear import Bear


class TestBear(unittest.TestCase):
    def setUp(self):
        self.tmp_config_path = mkstemp()[1]

        self.bear = Bear(settings_path=self.tmp_config_path)
        self.bear.config['settings']['db_path'] = ':memory:'
        self.bear.initialize_db()

    def tearDown(self):
        self.bear.db.close()
        os.remove(self.tmp_config_path)

    def test_add_feed(self):
        self.bear.add_feed('http://socketubs.org/atom.xml')
        self.assertEqual(self.bear.get_feeds().count(), 1)

    def test_get_feeds(self):
        feed_url = 'http://socketubs.org/atom.xml'
        self.bear.add_feed(feed_url)
        self.assertEqual(self.bear.get_feeds()[0].url, feed_url)
        self.assertEqual(self.bear.get_feeds()[0].id, 1)

    def test_get_feed_by_id(self):
        feed_url = 'http://socketubs.org/atom.xml'
        feed_id = self.bear.add_feed(feed_url)
        feed = self.bear.get_feed(feed_id=feed_id)
        self.assertEqual(feed.id, feed_id)

    def test_get_feed_by_url(self):
        feed_url = 'http://socketubs.org/atom.xml'
        self.bear.add_feed(feed_url)
        feed = self.bear.get_feed(url=feed_url)
        self.assertEqual(feed.url, feed_url)

if __name__ == '__main__':
    unittest.main()
