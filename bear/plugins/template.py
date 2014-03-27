# -*- coding: utf-8 -*-
"""
Description
===========
This plugin allow you to set a custom subject and message for your emails.
Template rendering is provided by Jinja2.

Install
=======
pip install jinja2

Example
=======
[plugin:template]
subject = test
template_file = /tmp/example.html
"""
import os
import sys
import logging

try:
    from jinja2 import Template
except ImportError:
    print('Template plugin need Jinja2 (pip install jinja2).')
    sys.exit(1)

from .base import BasePlugin

logger = logging.getLogger('plugins.template')


class TemplatePlugin(BasePlugin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template_file = self.config.get('template_file')
        self.subject_template = self.config.get('subject')

        if self.template_file is None:
            logger.debug('no template_file set')
        if self.subject_template is None:
            logger.debug('no subject set')

        if self.template_file and os.path.exists(self.template_file):
            self._load_template()
        elif self.template_file:
            logger.error('template_file does not exists')

    def _load_template(self):
        self.template = Template(open(self.config.get('template_file')).read())

    def pre_send_email(self, sender, to, subject, message, feed, feed_parsed, entry):
        if self.subject_template:
            subject = self.subject_template.format(feed=feed, entry=entry)
        if self.template_file:
            message = self.template.render(feed=feed, entry=entry)
        return sender, to, subject, message, feed, feed_parsed, entry

    def help(self):
        print(__doc__)
