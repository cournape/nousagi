# -*- coding: utf-8 -*-
# Copyright (c) 2015 David Cournapeau.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import

from characteristic import Attribute, attributes

from .var_loader import VarLoader


@attributes([
    Attribute("is_enabled", instance_of=bool),
    Attribute("coveragerc", instance_of=str),
])
class _CoverageConfiguration(object):
    @classmethod
    def from_json_dict(cls, data):
        return cls(
            is_enabled=data.get("enabled", False),
            coveragerc=data.get("coveragerc", "")
        )

    @property
    def prefix(self):
        prefix = ["coverage", "run", "-a"]
        if len(self.coveragerc) > 0:
            prefix.extend(["--rcfile", self.coveragerc])
        return " ".join(prefix)


class Config(object):
    """Container for the top-level test configuration.

    This contains all of the top-level configuration, such as the target
    host and variables to be used in test cases.

    """
    def __init__(self, variables, coverage, var_loader, test_filename):
        super(Config, self).__init__()
        self.var_loader = var_loader
        self.variables = variables
        self.test_filename = test_filename
        self.coverage = coverage

    @classmethod
    def from_dict(cls, config_data, test_filename):
        var_loader = VarLoader(test_filename)
        variables = var_loader.load_variables(config_data.get('vars', {}))
        coverage = _CoverageConfiguration.from_json_dict(
            config_data.get("coverage", {})
        )
        return cls(
            coverage=coverage,
            variables=variables,
            var_loader=var_loader,
            test_filename=test_filename,
        )

    def load_variable(self, name, var):
        return self.var_loader.load_variable(name, var, self.variables)
