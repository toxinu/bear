# -*- coding: utf-8 -*-
import smtplib
import feedparser
from time import mktime
from datetime import datetime
from peewee import SqliteDatabase
from email.mime.text import MIMEText

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from .plugins import PluginManager


class Bear:
    def __init__(self, settings_path="bear.ini"):
        self.settings_path = settings_path
        self.load_settings()
        self.load_plugins()

        self.smtp_host = self.config.get('email', 'host')
        self.smtp_port = self.config.getint('email', 'port')
        self.smtp_tls = self.config.getboolean('email', 'tls')
        self.smtp_user = self.config.get('email', 'user')
        self.smtp_pass = self.config.get('email', 'pass')

        self._smtp_conn = None

    @property
    def smtp_conn(self):
        if not self.config.get('email', 'to'):
            raise Exception('Missing "to" option in "email" section.')
        if self._smtp_conn is None:
            self._smtp_conn = smtplib.SMTP(self.smtp_host, self.smtp_port)
            self._smtp_conn.ehlo()
            if self.smtp_tls:
                self._smtp_conn.starttls()
            if self.smtp_user:
                self._smtp_conn.login(self.smtp_user, self.smtp_pass)
        return self._smtp_conn

    def load_plugins(self):
        conf = {}
        for plugin in self.config.get('settings', 'plugins').split(','):
            if plugin:
                conf[plugin] = {}
                if self.config.has_section('plugin:%s' % plugin):
                    conf[plugin] = self.config['plugin:%s' % plugin]
        self.plugin_manager = PluginManager(conf)

    def load_settings(self):
        self.config = ConfigParser()
        self.config.read(self.settings_path)

        # Settings
        if not self.config.has_section('settings'):
            self.config.add_section('settings')
        if not self.config.has_option('settings', 'db_path'):
            self.config.set('settings', 'db_path', 'bear.db')
        if not self.config.has_option('settings', 'plugins'):
            self.config.set('settings', 'plugins', '')

        # Email
        if not self.config.has_section('email'):
            self.config.add_section('email')
        if not self.config.has_option('email', 'from'):
            self.config.set('email', 'from', 'bear@localhost')
        if not self.config.has_option('email', 'to'):
            self.config.set('email', 'to', '')
        if not self.config.has_option('email', 'host'):
            self.config.set('email', 'host', 'localhost')
        if not self.config.has_option('email', 'port'):
            self.config.set('email', 'port', '25')
        if not self.config.has_option('email', 'tls'):
            self.config.set('email', 'tls', 'False')
        if not self.config.has_option('email', 'user'):
            self.config.set('email', 'user', '')
        if not self.config.has_option('email', 'pass'):
            self.config.set('email', 'pass', '')

    def initialize_config(self):
        self.config.write(open(self.settings_path, 'w'))

    def initialize_db(self):
        self.db = SqliteDatabase(
            self.config.get('settings', 'db_path'))
        self.db.connect()

        global DB
        DB = self.db

        from .feed import Feed
        if not Feed.table_exists():
            Feed.create_table()

    def add_feed(self, url):
        self.plugin_manager.run_signal('pre_add_feed', url)

        from .feed import Feed
        if not Feed.select(Feed.url).where(Feed.url == url).count():
            f = Feed(url=url)
            f.save()
            self.plugin_manager.run_signal('post_add_feed', f)
            return f.id
        self.plugin_manager.run_signal('post_add_feed', None)
        return None

    def delete_feed(self, feed_id=None):
        feed = self.get_feed(feed_id=feed_id)
        self.plugin_manager.run_signal('pre_delete_feed', feed)

        if feed is not None:
            feed.delete_instance()
        self.plugin_manager.run_signal('post_delete_feed', feed)

    def get_feed(self, feed_id=None, url=None):
        from .feed import Feed
        assert any(v is not None for v in [feed_id, url])

        if feed_id is not None:
            try:
                return Feed.select().where(Feed.id == feed_id).get()
            except Feed.DoesNotExist:
                return None
        try:
            return Feed.select().where(Feed.url == url).get()
        except Feed.DoesNotExist:
            return None

    def get_feeds(self):
        from .feed import Feed
        return Feed.select()

    def reset_feed(self, feed_id=None):
        feed = self.get_feed(feed_id=feed_id)
        self.plugin_manager.run_signal('pre_reset_feed', feed)

        if feed is not None:
            feed.updated = None
            feed.save()

        self.plugin_manager.run_signal('post_reset_feed', feed)

    def send_email(self, feed):
        self.plugin_manager.run_signal('pre_send_email', feed)

        msg = MIMEText(feed.description, 'html')
        msg['Subject'] = feed.title
        msg['From'] = self.config.get('email', 'from')
        msg['To'] = self.config.get('email', 'to')
        self.smtp_conn.sendmail(msg['From'], msg['To'].split(','), msg.as_string())

    def fetch_feed(self, feed_id=None):
        feed = self.get_feed(feed_id=feed_id)

        if feed is not None:
            print('[%s] Fetching %s ...' % (feed.id, feed.url))
            d = feedparser.parse(feed.url)
            updated = d.feed.get('updated_parsed') or d.feed.get('published_parsed')
            updated = datetime.fromtimestamp(mktime(updated))

            if feed.updated is not None and updated >= feed.updated:
                print('[%s] No updates found' % feed.id)
            else:
                d.entries.reverse()
                for e in d.entries:
                    print('    - %s' % e.title)
                    self.send_email(e)

            feed.updated = updated
            feed.save()
