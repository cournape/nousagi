# -*- coding: utf-8 -*-
# Copyright (c) 2015 David Cournapeau
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

import logging
import os

from haas.plugins.discoverer import match_path
from haas.plugins.i_discoverer_plugin import IDiscovererPlugin

from .yaml_test_loader import YamlTestLoader

logger = logging.getLogger(__name__)


class CLITestDiscoverer(IDiscovererPlugin):
    """A ``haas`` test discovery plugin to generate CLI test cases from
    YAML descriptions.

    Parameters
    ----------
    loader : haas.loader.Loader
        The ``haas`` test loader.

    """

    def __init__(self, loader, **kwargs):
        super(CLITestDiscoverer, self).__init__(**kwargs)
        self._loader = loader
        self._yaml_loader = YamlTestLoader(loader)

    @classmethod
    def from_args(cls, args, arg_prefix, loader):
        """Construct the discoverer from parsed command line arguments.

        Parameters
        ----------
        args : argparse.Namespace
            The ``argparse.Namespace`` containing parsed arguments.
        arg_prefix : str
            The prefix used for arguments beloning solely to this plugin.
        loader : haas.loader.Loader
            The test loader used to construct TestCase and TestSuite instances.

        """
        return cls(loader)

    @classmethod
    def add_parser_arguments(cls, parser, option_prefix, dest_prefix):
        """Add options for the plugin to the main argument parser.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            The parser to extend
        option_prefix : str
            The prefix that option strings added by this plugin should use.
        dest_prefix : str
            The prefix that ``dest`` strings for options added by this
            plugin should use.

        """

    def discover(self, start, top_level_directory=None, pattern=None):
        """Discover YAML-formatted Web API tests.

        Parameters
        ----------
        start : str
            Directory from which to recursively discover test cases.
        top_level_directory : None
            Ignored; for API compatibility with haas.
        pattern : None
            Ignored; for API compatibility with haas.

        """
        if os.path.isdir(start):
            start_directory = start
            return self._discover_by_directory(start_directory)
        elif os.path.isfile(start):
            start_filepath = start
            return self._discover_by_file(start_filepath)
        return self._loader.create_suite()

    def _discover_by_directory(self, start_directory):
        """Run test discovery in a directory.

        Parameters
        ----------
        start_directory : str
            The package directory in which to start test discovery.

        """
        start_directory = os.path.abspath(start_directory)
        tests = self._discover_tests(start_directory)
        return self._loader.create_suite(list(tests))

    def _discover_by_file(self, start_filepath):
        """Run test discovery on a single file.

        Parameters
        ----------
        start_filepath : str
            The module file in which to start test discovery.

        """
        start_filepath = os.path.abspath(start_filepath)
        logger.debug('Discovering tests in file: start_filepath=%r',
                     start_filepath)

        tests = self._load_from_file(start_filepath)
        return self._loader.create_suite(list(tests))

    def _load_from_file(self, filepath):
        logger.debug('Loading tests from %r', filepath)
        tests = self._yaml_loader.load_tests_from_file(filepath)
        return self._loader.create_suite(tests)

    def _discover_tests(self, start_directory):
        pattern = 'test*.yml'
        for curdir, dirnames, filenames in os.walk(start_directory):
            logger.debug('Discovering tests in %r', curdir)
            for filename in filenames:
                filepath = os.path.join(curdir, filename)
                if not match_path(filename, filepath, pattern):
                    logger.debug('Skipping %r', filepath)
                    continue
                yield self._load_from_file(filepath)
