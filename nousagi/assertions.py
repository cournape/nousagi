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
        return case.assertRegexpMatches(output.rstrip(), self.render())
