import os
import string
import subprocess

from characteristic import Attribute, attributes

from .assertions import (
    OutputAssertion, OutputStartswithAssertion, RegexOutputAssertion, StatusAssertion
)
from .pre_runs import (
    Command, Env, Mkdtemp, RegisterVariable, State, WriteFileFromTemplate
)


@attributes([
    Attribute("name", instance_of=str),
    Attribute("cmd", instance_of=str),
    Attribute("assertions", instance_of=list),
    Attribute("pre_runs", instance_of=list),
    Attribute("post_runs", instance_of=list),
    Attribute("variables", instance_of=dict),
])
class Test(object):
    @classmethod
    def from_json_dict(cls, variables, data):
        assertions = []
        pre_runs = []
        post_runs = []

        commands = {
            "mkdtemp": Mkdtemp,
            "write_file": WriteFileFromTemplate,
        }

        if "pre_runs" in data:
            for pre_run_data in data["pre_runs"]:
                if pre_run_data["type"] == "command":
                    command_klass = commands.get(pre_run_data["command"])
                    if command_klass is None:
                        msg = "Unknown command {!r}".format(command_klass)
                        raise NotImplementedError(msg)
                    command = command_klass.from_json_dict(pre_run_data)

                    registers_data = pre_run_data.get("register", [])

                    registers = tuple(
                        RegisterVariable.from_json_dict(register_data)
                        for register_data in registers_data
                    )

                    pre_run = Command(command, command.ReturnState, registers)
                elif pre_run_data["type"] == "env":
                    pre_run = Env.from_json_dict(pre_run_data)
                else:
                    msg = ("Unsupported type of pre run: {!r}".
                           format(pre_run_data["type"]))
                    raise NotImplementedError(msg)
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
            pre_runs=pre_runs, post_runs=post_runs, variables=variables
        )

    def run(self, case):
        state = State(variables=self.variables, environ=os.environ.copy())

        return_states = []
        for pre_run in self.pre_runs:
            return_state = pre_run.run(state)
            return_states.append(return_state)
            pre_run.update(state, return_state)

        try:
            self._run_command(case, state)
        finally:
            for post_run in self.post_runs:
                post_run.run(state)
            for return_state in reversed(return_states):
                return_state.cleanup()

    def _run_command(self, case, state):
        cmd = string.Template(self.cmd).substitute(**state.variables)

        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            stdin=subprocess.PIPE, shell=True, env=state.environ
        )
        stdout, stderr = p.communicate()

        for assertion in self.assertions:
            assertion.uphold(state.variables, case, stdout, stderr, p.returncode)
