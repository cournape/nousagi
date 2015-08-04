import abc
import os.path
import string
import subprocess

from characteristic import Attribute, attributes
from haas.utils import abstractclassmethod
from six import add_metaclass


@add_metaclass(abc.ABCMeta)
class IAssertion(object):
    @abstractclassmethod
    def from_json_dict(cls, variables, data):
        """Create the assertion from a variables set and the loaded json
        dict.
        """
        # We call cls to ensure a subclass not implementing this class method
        # cannot be created
        return cls()

    @abc.abstractmethod
    def uphold(self, variables, case, stdout, stder, returncode):
        """ The method to call to check the assertion."""


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=int)
])
class StatusAssertion(IAssertion):
    @classmethod
    def from_json_dict(cls, variables, data):
        return cls(variables=variables, expected=data["expected"])

    def uphold(self, variables, case, stdout, stderr, returncode):
        case.assertEqual(self.expected, returncode)


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=str)
])
class OutputAssertion(IAssertion):
    @classmethod
    def from_json_dict(cls, variables, data):
        return cls(variables=variables, expected=data["output"])

    def uphold(self, variables, case, stdout, stderr, returncode):
        output = "\n".join((stdout, stderr))
        case.assertTrue(output.startswith(self._render()))

    def _render(self):
        return string.Template(self.expected).substitute(self.variables)


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=str)
])
class OutputStartswithAssertion(IAssertion):
    @classmethod
    def from_json_dict(cls, variables, data):
        return cls(variables=variables, expected=data["expected"])

    def render(self):
        return string.Template(self.expected).substitute(self.variables)

    def uphold(self, variables, case, stdout, stderr, returncode):
        output = "\n".join((stdout, stderr))
        case.assertTrue(output.startswith(self.render()))


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=str)
])
class RegexOutputAssertion(IAssertion):
    @classmethod
    def from_json_dict(cls, variables, data):
        return cls(variables=variables, expected=data["expected"])

    def uphold(self, variables, case, stdout, stderr, returncode):
        output = "\n".join((stdout, stderr))
        return case.assertRegexpMatches(output.rstrip(), self._render().rstrip())

    def _render(self):
        return string.Template(self.expected).substitute(self.variables)


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("path", instance_of=str),
    Attribute("exists", instance_of=bool)
])
class FileExists(IAssertion):
    @classmethod
    def from_json_dict(cls, variables, data):
        return cls(
            variables=variables, path=data["path"], exists=data["exists"]
        )

    def uphold(self, variables, case, stdout, stderr, returncode):
        path = self._render_path()
        if self.exists:
            msg = "File {0!r} does not exist".format(path)
            case.assertTrue(os.path.exists(path), msg)
        else:
            msg = "File {0!r} exists".format(path)
            case.assertFalse(os.path.exists(path), msg)

    def _render_path(self):
        return string.Template(self.path).substitute(self.variables)


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("status", instance_of=int),
    Attribute("command", instance_of=str),
    Attribute("assertions", instance_of=list)
])
class CommandAssertion(IAssertion):
    @classmethod
    def from_json_dict(cls, variables, data):
        generic_assertions_factory = {
            "regex": RegexOutputAssertion,
            "file": FileExists,
        }

        assertions = []

        for assertion_data in data.get("assertions", []):
            kind = assertion_data["type"]
            factory = generic_assertions_factory.get(kind)
            if factory is None:
                msg = "Assertion type {0!r} not supported"
                raise NotImplementedError(msg.format(assertion_data["type"]))
            else:
                assertion = factory.from_json_dict(variables, assertion_data)
                assertions.append(assertion)

        return cls(
            variables=variables, status=data["status"],
            command=data["command"], assertions=assertions,
        )

    def uphold(self, variables, case, stdout, stderr, returncode):
        command = self._render_command()
        p = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True,
        )
        stdout, stderr = p.communicate()

        for assertion in self.assertions:
            assertion.uphold(variables, case, stdout, stderr, p.returncode)

    def _render_command(self):
        return string.Template(self.command).substitute(self.variables)
