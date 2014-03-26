# -*- coding: utf-8 -*-
from jinja2 import Template
from .base import BasePlugin


class TemplatePlugin(BasePlugin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_template()

    def _load_template(self):
        self.template = Template(open(self.config.get('template_file')).read())

    def pre_send_email(self, sender, to, subject, message, feed, entry):
        subject = self.config.get('subject').format(feed=feed, entry=entry)
        message = self.template.render(feed=feed, entry=entry)
        return sender, to, subject, message, feed, entry
