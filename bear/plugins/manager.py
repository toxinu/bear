# -*- coding: utf-8 -*-
import logging
from importlib import import_module

logger = logging.getLogger('pluginmanager')


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

    def get_plugin_help(self, name):
        if self.plugins.get(name):
            return self.plugins.get(name).help()
        else:
            logger.info('[plugin-%s] not exists' % name)

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
                msg = '[plugin-%s] %s (args:%s)' % (name, signal, args)
                if len(msg) > 90:
                    msg = msg[:90] + ' [...truncated...]'
                logger.debug(msg)
                # If plugin method doesn't return initial count of
                # args sent by Bear, ignore this plugin work
                if len(_args) != args_count:
                    logger.error('[plugin-%s] %s not return good number of args (ignored)' % (
                        name, signal))
                else:
                    args = _args
            except NotImplementedError:
                logger.debug('[plugin-%s] %s not implemented' % (name, signal))
        # If latest plugin return only one item it must
        # be converted in tuple to be unpacked by Bear
        if args_count > 1:
            return tuple(args)
        return args[0]
