# -*- coding: utf-8 -*-
# Copyright (c) 2015 David Cournapeau.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from six import string_types
from stevedore.extension import ExtensionManager

from .exceptions import InvalidVariable, InvalidVariableType, VariableLoopError


class StringVarLoader(object):
    def __init__(self, name, value):
        super(StringVarLoader, self).__init__()
        self.name = name
        self.value = value

    def load(self, filename, variables):
        return True


class VarLoader(object):
    def __init__(self, filename):
        super(VarLoader, self).__init__()
        self.filename = filename
        loaders = ExtensionManager(
            namespace='nousagi.var_loaders',
        )
        self.loaders = dict(
            (name, loaders[name].plugin)
            for name in loaders.names()
        )
        self.loader_keys = set(self.loaders.keys())

    def _create_loader(self, name, var):
        if isinstance(var, string_types):
            loader = StringVarLoader(name, var)
        elif isinstance(var, dict):
            try:
                loader_type = var['type']
            except KeyError:
                raise InvalidVariableType(
                    'Missing type for var {0!r}'.format(name))
            if loader_type not in self.loaders:
                raise InvalidVariableType(
                    'Invalid type for var {0!r}: {1!r}'.format(
                        name, loader_type))
            cls = self.loaders[loader_type]
            loader = cls.from_dict(name, var)
        else:
            raise InvalidVariable(name, repr(var))
        return loader

    def _create_loaders(self, var_dict):
        loaders = []
        for name, var in var_dict.items():
            loaders.append(self._create_loader(name, var))
        return loaders

    def load_variable(self, name, var, existing_variables):
        loader = self._create_loader(name, var)
        if not loader.load(self.filename, existing_variables):
            raise InvalidVariable(name, repr(var))
        return loader.value

    def load_variables(self, var_dict):
        variables = {}
        loaders = self._create_loaders(var_dict)
        while len(loaders) > 0:
            loaded = set(loader for loader in loaders
                         if loader.load(self.filename, variables))
            if len(loaded) == 0:
                raise VariableLoopError()
            new_vars = ((loader.name, loader.value) for loader in loaded)
            variables.update(new_vars)
            loaders = [loader for loader in loaders if loader not in loaded]
        return variables
