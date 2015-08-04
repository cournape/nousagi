import subprocess
import sys
import unittest

import six
import yaml

from .config import Config
from .pre_runs import MultiSteps, pre_run_factory_from_json_dict
from .test import Scenario, Test


TEST_NAME_ATTRIBUTE = 'nousagi_name'


def _create_test_method(test):
    def test_method(self):
        test.run(self)

    setattr(test_method, TEST_NAME_ATTRIBUTE, test.name)

    return test_method


def create_test_case_for_case(filename, config, case, pre_run_definitions):
    """Programatically generate ``TestCases`` from a test specification.

    Returns
    -------
    test_case_cls : type
        A subclass of ``unittest.TestCase`` containing all of the
        generated tests, in the same order as defined in the file.

    """
    pre_runs = [
        pre_run_definitions[name]
        for name in case.get('setup', [])
    ]
    post_runs = []
    tests = [
        Test.from_json_dict(config, spec, pre_runs, post_runs)
        for spec in case.get('tests', [])
    ]
    tests += [
        Scenario.from_json_dict(config, spec, pre_runs, post_runs)
        for spec in case.get('scenarios', [])
    ]
    test_count = len(tests)
    class_dict = dict(
        ('test_{index:0>{test_count}}'.format(
            index=index, test_count=test_count),
         _create_test_method(test))
        for index, test in enumerate(tests)
    )
    class_dict[TEST_NAME_ATTRIBUTE] = case['name']

    if 'max-diff' in case:
        class_dict['maxDiff'] = case['max-diff']

    def __str__(self):
        method = getattr(self, self._testMethodName)
        template = '{0!r} ({1})'
        test_name = '{0}:{1}'.format(getattr(self, TEST_NAME_ATTRIBUTE),
                                     getattr(method, TEST_NAME_ATTRIBUTE))
        str_filename = filename
        if six.PY2:
            encoding = sys.getdefaultencoding()
            template = template.encode(encoding)
            test_name = test_name.encode(encoding)
            if isinstance(str_filename, six.text_type):
                str_filename = filename.encode(encoding)
        return template.format(
            test_name,
            str_filename,
        )

    class_dict['__str__'] = __str__

    class_name = 'GeneratedYamlTestCase'
    if six.PY2:
        class_name = class_name.encode('ascii')
    return type(class_name, (unittest.TestCase,), class_dict)


def create_pre_run_set(filename, config, pre_run_set):
    pre_runs = [
        pre_run_factory_from_json_dict(step)
        for step in pre_run_set
    ]

    return MultiSteps(steps=pre_runs)


class YamlTestLoader(object):
    """A test case generator, creating ``TestCase`` and ``TestSuite``
    instances from a single YAML file.

    Parameters
    ----------
    loader : haas.loader.Loader
        The ``haas`` test loader.

    """

    def __init__(self, loader):
        super(YamlTestLoader, self).__init__()
        self._loader = loader

    def load_tests_from_file(self, filename):
        """Load the YAML test file and create a ``TestSuite`` containing all
        test cases contained in the file.

        """
        with open(filename) as fh:
            test_structure = yaml.safe_load(fh)
        return self.load_tests_from_yaml(test_structure, filename)

    def load_tests_from_yaml(self, test_structure, filename):
        """Create a ``TestSuite`` containing all test cases contained in the
        yaml structure.

        """
        loader = self._loader

        config = Config.from_dict(test_structure.get('config', {}), filename)
        if config.coverage.is_enabled and config.coverage.reset:
            cmd = ["coverage", "erase"]
            if config.coverage.coveragerc:
                cmd += ["--rcfile", config.coverage.coveragerc]
            subprocess.check_output(cmd)

        pre_run_definitions = dict(
            (name, create_pre_run_set(filename, config, pre_run_set))
            for name, pre_run_set
            in test_structure.get("pre_run_definitions", {}).items()
        )

        cases = (
            create_test_case_for_case(
                filename, config, case, pre_run_definitions
            )
            for case in test_structure['cases']
        )
        tests = [loader.load_case(case) for case in cases]
        return loader.create_suite(tests)
