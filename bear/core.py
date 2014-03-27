# -*- coding: utf-8 -*-
import sys
import logging
import smtplib
import feedparser
from time import mktime
from datetime import datetime
from peewee import SqliteDatabase
from email.mime.text import MIMEText
from colorlog import ColoredFormatter

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from .plugins import PluginManager

PY2 = sys.version_info[0] == 2


class Bear:
    def __init__(self, settings_path="bear.ini", cli_opts={}):
        self.cli_opts = cli_opts
        self.settings_path = settings_path
        self.load_settings()
        self.load_cli_options()
        self.load_logger()
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

    def load_cli_options(self):
        if self.cli_opts.get('--log-level'):
            self.config['settings']['log_level'] = self.cli_opts.get('--log-level')
        if self.cli_opts.get('--no-email'):
            self.config['email']['to'] = ''

    def load_logger(self):
        level = self.config.get('settings', 'log_level').lower()

        if level == "debug":
            level = logging.DEBUG
        elif level == "error":
            level = logging.ERROR
        else:
            level = logging.INFO

        opts = {'level': level}

        if self.config.get('settings', 'log_file'):
            opts.update({
                'filename': self.config.get('settings', 'log_file'),
                'format': '%(asctime)s %(name)s:%(levelname)-5s %(message)s',
                'datefmt': '%m-%d %H:%M'})

        logging.basicConfig(**opts)

        console = logging.StreamHandler()
        console.setLevel(level)

        logger_format = "%(log_color)s%(message)s"
        if level == logging.DEBUG:
            logger_format = '%(log_color)s%(name)s:%(levelname)-5s %(message)s'
        formatter = ColoredFormatter(
            logger_format,
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red'})
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

        self.logger = logging.getLogger('bear')

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
        if not self.config.has_option('settings', 'log_file'):
            self.config.set('settings', 'log_file', 'bear.log')
        if not self.config.has_option('settings', 'log_level'):
            self.config.set('settings', 'log_level', 'INFO')

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
        url = self.plugin_manager.run_signal('pre_add_feed', url)

        from .feed import Feed
        if not Feed.select(Feed.url).where(Feed.url == url).count():
            f = Feed(url=url)
            f.save()
            f = self.plugin_manager.run_signal('post_add_feed', f)
            self.logger.info('[feed-%s] added (%s)' % (f.id, f.url))
            return f.id
        f = self.plugin_manager.run_signal('post_add_feed', None)
        feed = Feed.select().where(Feed.url == url).get()
        self.logger.info('[feed-%s] already exists (%s)' % (feed.id, feed.url))
        return f

    def delete_feed(self, feed_id=None):
        feed = self.get_feed(feed_id=feed_id)
        feed = self.plugin_manager.run_signal('pre_delete_feed', feed)

        if feed is not None:
            self.logger.info('[feed-%s] deleted (%s)' % (feed.id, feed.url))
            feed.delete_instance()
        else:
            self.logger.info('[feed-%s] not exists' % feed_id)

        feed = self.plugin_manager.run_signal('post_delete_feed', feed)

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
        self.logger.debug('[feed-%s] Fire pre_reset_feed event' % feed_id)
        feed = self.plugin_manager.run_signal('pre_reset_feed', feed)

        if feed is not None:
            feed.updated = None
            feed.save()
            self.logger.info('[feed-%s] reseted' % feed.id)
        else:
            self.logger.info('[feed-%s] not exists' % feed_id)

        feed = self.plugin_manager.run_signal('post_reset_feed', feed)

    def send_email(self, feed, feed_parsed, entry):
        (sender, to, subject, message,
            feed, feed_parsed, entry) = self.plugin_manager.run_signal(
            'pre_send_email',
            self.config.get('email', 'from'),
            self.config.get('email', 'to'),
            '[%s] %s' % (feed_parsed.feed.title, entry.title),
            entry.description,
            feed,
            feed_parsed,
            entry)

        if PY2:
            message = message.encode('utf-8')
        msg = MIMEText(message, 'html')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to
        if self.config.get('email', 'to'):
            self.smtp_conn.sendmail(sender, to.split(','), msg.as_string())
            return True
        return False

    def fetch_feed(self, feed_id=None):
        feed = self.get_feed(feed_id=feed_id)
        email_count = 0

        if feed is not None:
            self.logger.info('[feed-%s] fetching feed (%s)' % (feed.id, feed.url))
            d = feedparser.parse(feed.url)
            updated = d.feed.get('updated_parsed') or d.feed.get('published_parsed')

            if updated is None:
                self.logger.error('[feed-%s] not well formatted (ignored)' % feed.id)
                return
            updated = datetime.fromtimestamp(mktime(updated))

            if feed.updated is not None and updated >= feed.updated:
                self.logger.info('[feed-%s] no updates found' % feed.id)
            else:
                self.logger.info('[feed-%s] %s updates found' % (feed.id, len(d.entries)))
                d.entries.reverse()
                for e in d.entries:
                    self.logger.debug('[feed-%s] %s' % (feed.id, e.title))
                    r = self.send_email(feed, d, e)
                    if r:
                        email_count += 1

            self.logger.info('[feed-%s] %s email(s) sent' % (feed.id, email_count))
            feed.updated = updated
            feed.save()
        else:
            self.logger.info('[feed-%s] not exists' % feed_id)
