import string
import subprocess

from characteristic import Attribute, attributes

from .assertions import (
    OutputAssertion, OutputStartswithAssertion, RegexOutputAssertion, StatusAssertion
)


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("cmd", instance_of=str),
])
class PreRunCommand(object):
    def render(self):
        return string.Template(self.cmd).substitute(self.variables)


@attributes([
    Attribute("name", instance_of=str),
    Attribute("cmd", instance_of=str),
    Attribute("assertions", instance_of=list),
    Attribute("pre_runs", instance_of=list),
    Attribute("variables", instance_of=dict),
])
class Test(object):
    @classmethod
    def from_json_dict(cls, variables, data):
        assertions = []
        pre_runs = []

        if "pre_runs" in data:
            for pre_run_data in data["pre_runs"]:
                pre_run = PreRunCommand(
                    variables=variables, cmd=pre_run_data["cmd"]
                )
                pre_runs.append(pre_run)

        if "assertions" in data:
            for assertion_data in data["assertions"]:
                if assertion_data["type"] == "regex":
                    assertion = RegexOutputAssertion(
                        variables=variables,
                        expected=assertion_data["expected"]
                    )
                    assertions.append(assertion)
                elif assertion_data["type"] == "startswith":
                    assertion = OutputStartswithAssertion(
                        variables=variables,
                        expected=assertion_data["expected"]
                    )
                    assertions.append(assertion)
                else:
                    raise NotImplementedError()

        if "status" in data:
            assertion = StatusAssertion(
                variables=variables, expected=data["status"]
            )
            assertions.append(assertion)
        if "output" in data:
            assertion = OutputAssertion(
                variables=variables, expected=data["output"]
            )
            assertions.append(assertion)

        return cls(
            name=data["name"], cmd=data["cmd"], assertions=assertions,
            pre_runs=pre_runs, variables=variables
        )

    def run(self, case):
        cmd = string.Template(self.cmd).substitute(**self.variables)

        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.PIPE, shell=True
        )
        stdout, stderr = p.communicate()

        for assertion in self.assertions:
            assertion.uphold(self.variables, case, stdout, stderr, p.returncode)
