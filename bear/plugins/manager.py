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
        # Get initial args given by Bear to
        # check if plugin return good number
        args_count = len(args)

        for name, plugin in self.plugins.items():
            try:
                _args = getattr(plugin, signal)(*args)
                # If plugin method return only one item it must
                # be converted in tuple for following plugin
                if not isinstance(_args, tuple):
                    _args = (_args, )
                msg = '[%s] %s (args:%s)' % (signal, name, args)
                if len(msg) > 90:
                    msg = msg[:90] + ' [...truncated...]'
                print(msg)
                # If plugin method doesn't return initial count of
                # args sent by Bear, ignore this plugin work
                if len(_args) != args_count:
                    print('[%s] %s not return good number of args (ignored)' % (signal, name))
                else:
                    args = _args
            except NotImplementedError:
                print('[%s] %s not implemented' % (signal, name))
        # If latest plugin return only one item it must
        # be converted in tuple to be unpacked by Bear
        if args_count > 1:
            return tuple(args)
        return args[0]
