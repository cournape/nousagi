import os
import string
import subprocess

from characteristic import Attribute, attributes

from .assertions import (
    FileExists, OutputAssertion, OutputStartswithAssertion,
    RegexOutputAssertion, StatusAssertion
)
from .config import Config
from .pre_runs import State


def _run_pre_runs(pre_runs, state):
    return_states = []
    for pre_run in pre_runs:
        return_state = pre_run.run(state)
        return_states.append(return_state)
    return return_states


def _run_post_runs(post_runs, state, return_states):
    for post_run in post_runs:
        post_run.run(state)
    for return_state in reversed(return_states):
        return_state.cleanup()


@attributes([
    Attribute("name", instance_of=str),
    Attribute("cmd", instance_of=str),
    Attribute("assertions", instance_of=list),
    Attribute("pre_runs", instance_of=list),
    Attribute("post_runs", instance_of=list),
    Attribute("config", instance_of=Config),
])
class Test(object):
    @classmethod
    def from_json_dict(cls, config, data, pre_runs, post_runs):
        assertions = []
        pre_runs = pre_runs
        post_runs = post_runs

        if "status" in data:
            assertion = StatusAssertion(
                variables=config.variables, expected=data["status"]
            )
            assertions.append(assertion)
        if "output" in data:
            assertion = OutputAssertion(
                variables=config.variables, expected=data["output"]
            )
            assertions.append(assertion)

        if "assertions" in data:
            for assertion_data in data["assertions"]:
                if assertion_data["type"] == "regex":
                    assertion = RegexOutputAssertion(
                        variables=config.variables,
                        expected=assertion_data["expected"]
                    )
                    assertions.append(assertion)
                elif assertion_data["type"] == "startswith":
                    assertion = OutputStartswithAssertion(
                        variables=config.variables,
                        expected=assertion_data["expected"]
                    )
                    assertions.append(assertion)
                elif assertion_data["type"] == "file":
                    assertion = FileExists.from_json_dict(
                        config.variables, assertion_data
                    )
                    assertions.append(assertion)
                else:
                    msg = "Assertion type {0!r} not supported"
                    raise NotImplementedError(msg.format(assertion_data["type"]))

        return cls(
            name=data["name"], cmd=data["cmd"], assertions=assertions,
            pre_runs=pre_runs, post_runs=post_runs, config=config
        )

    def run(self, case):
        state = State(variables=self.config.variables, environ=os.environ.copy())
        return self.run_from_state(case, state)

    def run_from_state(self, case, state):
        return_states = _run_pre_runs(self.pre_runs, state)

        try:
            self._run_command(case, state)
        finally:
            _run_post_runs(self.post_runs, state, return_states)

    def _run_command(self, case, state):
        cmd = string.Template(self.cmd).substitute(**state.variables)
        if self.config.coverage.is_enabled:
            cmd = self.config.coverage.prefix + " " + cmd

        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.PIPE, shell=True, env=state.environ
        )
        stdout, stderr = p.communicate()

        for assertion in self.assertions:
            assertion.uphold(state.variables, case, stdout, stderr, p.returncode)


@attributes([
    Attribute("name", instance_of=str),
    Attribute("config", instance_of=Config),
    Attribute("tests", instance_of=list),
    Attribute("pre_runs", instance_of=list),
    Attribute("post_runs", instance_of=list),
])
class Scenario(object):
    @classmethod
    def from_json_dict(cls, config, data, pre_runs, post_runs):
        name = data["name"]

        tests = [
            Test.from_json_dict(config, step, [], [])
            for step in data["steps"]
        ]

        return cls(
            name=name, config=config, tests=tests, pre_runs=pre_runs,
            post_runs=post_runs
        )

    def run(self, case):
        state = State(variables=self.config.variables, environ=os.environ.copy())

        return_states = _run_pre_runs(self.pre_runs, state)
        try:
            for test in self.tests:
                test.run_from_state(case, state)
        finally:
            _run_post_runs(self.post_runs, state, return_states)
