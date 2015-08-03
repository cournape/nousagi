# -*- coding: utf-8 -*-
# Copyright (c) 2015 David Cournapeau.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from .var_loader import VarLoader


class Config(object):
    """Container for the top-level test configuration.

    This contains all of the top-level configuration, such as the target
    host and variables to be used in test cases.

    """
    def __init__(self, variables, var_loader, test_filename):
        super(Config, self).__init__()
        self.var_loader = var_loader
        self.variables = variables
        self.test_filename = test_filename

    @classmethod
    def from_dict(cls, config_data, test_filename):
        var_loader = VarLoader(test_filename)
        variables = var_loader.load_variables(config_data.get('vars', {}))
        return cls(
            variables=variables,
            var_loader=var_loader,
            test_filename=test_filename,
        )

    def load_variable(self, name, var):
        return self.var_loader.load_variable(name, var, self.variables)
