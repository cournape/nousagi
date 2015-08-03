import os
import string
import subprocess

import yaml

import jaguar

from .assertions import (
    OutputAssertion, OutputStartswithAssertion, RegexOutputAssertion, StatusAssertion
)
from .test import Test


def execute_test(test, variables):
    cmd = string.Template(test.cmd).substitute(**variables)

    environ = os.environ.copy()

    for pre_run in test.pre_runs:
        subprocess.check_call(
            pre_run.render(), shell=True, env=environ,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        stdin=subprocess.PIPE, shell=True, env=environ
    )
    stdout, stderr = p.communicate()

    output = "\n".join((stdout, stderr))

    for assertion in test.assertions:
        if isinstance(assertion, StatusAssertion):
            uphold = assertion.uphold(p.returncode)
            if not uphold:
                print(output)
            print("        status == {}: {}".format(
                assertion.expected, uphold
            ))
        elif isinstance(assertion,
                        (OutputAssertion, RegexOutputAssertion,
                         OutputStartswithAssertion)):
            uphold = assertion.uphold(output)
            if not uphold:
                print(output.rstrip(), assertion.render())
            print("        output: {}".format(assertion.uphold(output)))
        else:
            raise NotImplementedError()


def main():
    with open("description.yaml", "rt") as fp:
        data = yaml.load(fp)

    variables = {
        "cmd": "jaguar",
        "version": jaguar.__version__
    }

    for case_data in data.get("cases", []):
        name = case_data["name"]
        print("Case: {!r}".format(name))
        for test_data in case_data.get("tests", []):
            test = Test.from_json_dict(variables, test_data)
            print("    {!r}".format(test.name))
            execute_test(test, variables)
