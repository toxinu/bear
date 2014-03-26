# -*- coding: utf-8 -*-
from importlib import import_module


class PluginManager:
    def __init__(self, conf):
        self.conf = conf
        self.load_plugins()

    def load_plugins(self):
        self.plugins = {}
        for plugin in self.conf:
            plugin_class = getattr(import_module(
                'bear.plugins.%s' % plugin), '%sPlugin' % plugin.title())
            self.plugins[plugin] = plugin_class(**self.conf[plugin])

    def run_signal(self, signal, *args):
        for name, plugin in self.plugins.items():
            try:
                getattr(plugin, signal)(*args)
                print('[%s] %s' % (signal, name))
            except NotImplementedError:
                print('[%s] %s not implemented' % (signal, name))
