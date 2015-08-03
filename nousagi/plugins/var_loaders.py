# -*- coding: utf-8 -*-
# Copyright (c) 2015 David Cournapeau.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import os
import os.path
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


class ExecutableVarLoader(IVarLoader):
    def __init__(self, name, executable):
        super(ExecutableVarLoader, self).__init__()
        self.name = name
        self._executable = executable
        self._value = None
        self._is_loaded = False

    @classmethod
    def from_dict(cls, name, var_dict):
        return cls(name=name, executable=var_dict['executable'])

    def load(self, filename, variables):
        if not self._is_loaded:
            self._value = _which(self._executable)
            self._is_loaded = True
        return self._is_loaded

    @property
    def value(self):
        return self._value


def _which(fn):
    """Simplified version of shutil.which
    """

    def _access_check(fn):
        return (os.path.exists(fn) and os.access(fn, os.F_OK | os.X_OK)
                and not os.path.isdir(fn))
    pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
    files = [fn + ext.lower() for ext in pathext]
    path = os.environ.get("PATH", os.defpath).split(os.pathsep)
    seen = set()
    for dir in map(os.path.normcase, path):
        if dir not in seen:
            seen.add(dir)
            for name in map(lambda f: os.path.join(dir, f), files):
                if _access_check(name):
                    return name
