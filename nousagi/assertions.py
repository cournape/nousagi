import os.path
import string

from characteristic import Attribute, attributes


class Assertion(object):
    pass


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=int)
])
class StatusAssertion(Assertion):
    def uphold(self, variables, case, stdout, stderr, returncode):
        case.assertEqual(self.expected, returncode)


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=str)
])
class OutputAssertion(Assertion):
    def render(self):
        return string.Template(self.expected).substitute(self.variables)

    def uphold(self, variables, case, stdout, stderr, returncode):
        output = "\n".join((stdout, stderr))
        case.assertTrue(output.startswith(self.render()))


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=str)
])
class OutputStartswithAssertion(Assertion):
    def render(self):
        return string.Template(self.expected).substitute(self.variables)

    def uphold(self, variables, case, stdout, stderr, returncode):
        output = "\n".join((stdout, stderr))
        case.assertTrue(output.startswith(self.render()))


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=str)
])
class RegexOutputAssertion(Assertion):
    def render(self):
        return string.Template(self.expected).substitute(self.variables)

    def uphold(self, variables, case, stdout, stderr, returncode):
        output = "\n".join((stdout, stderr))
        return case.assertRegexpMatches(output.rstrip(), self.render().rstrip())


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("path", instance_of=str),
    Attribute("exists", instance_of=bool)
])
class FileExists(Assertion):
    @classmethod
    def from_json_dict(cls, variables, data):
        return cls(
            variables=variables, path=data["path"], exists=data["exists"]
        )

    def _render_path(self):
        return string.Template(self.path).substitute(self.variables)

    def uphold(self, variables, case, stdout, stderr, returncode):
        path = self._render_path()
        if self.exists:
            msg = "File {0!r} does not exist".format(path)
            case.assertTrue(os.path.exists(path), msg)
        else:
            msg = "File {0!r} exists".format(path)
            case.assertFalse(os.path.exists(path), msg)
