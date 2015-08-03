# -*- coding: utf-8 -*-
# Copyright (c) 2015 David Cournapeau.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import subprocess

from .i_var_loader import IVarLoader


class CommandVarLoader(IVarLoader):
    def __init__(self, name, command):
        super(CommandVarLoader, self).__init__()
        self.name = name
        self._command = command
        self._value = None
        self._is_loaded = False

    @classmethod
    def from_dict(cls, name, var_dict):
        return cls(name=name, command=var_dict['command'])

    def load(self, filename, variables):
        if not self._is_loaded:
            output = subprocess.check_output(self._command, shell=True)
            self._value = output.rstrip()
            self._is_loaded = True
        return self._is_loaded

    @property
    def value(self):
        return self._value
