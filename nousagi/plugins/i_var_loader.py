# -*- coding: utf-8 -*-
# Copyright (c) 2014 Simon Jagoe and Enthought Ltd.
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import abc

from six import add_metaclass

from haas.utils import abstractclassmethod


@add_metaclass(abc.ABCMeta)
class IVarLoader(object):

    @abstractclassmethod
    def from_dict(cls, name, var_dict):
        """Create the VarLoader instance from a var name and var value
        dictionary.

        Parameters
        ----------
        name : str
            The name of the var.
        var_dict: dict
            The value of the var before loading.

        """

    @abc.abstractmethod
    def load(self, filename, variables):
        """Load the var, making use of already-loaded vars in the dict
        ``variables``.

        Parameters
        ----------
        filename : str
            The path of the file from which this var is loaded.
        variables : dict
            Mapping of var names to their loaded values.

        Returns
        -------
        is_loaded : bool
            ``True`` if the var has been successfully loaded and the
            value is now accessible via the ``value``
            attribute. ``False`` if the var is missing prerequisite
            values in the ``variables`` dict and needs to be loaded at a
            later stage after dependencies are resolved.

        """
