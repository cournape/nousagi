import re
import string

from characteristic import Attribute, attributes


class Assertion(object):
    pass


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=int)
])
class StatusAssertion(Assertion):
    def uphold(self, actual):
        return self.expected == actual


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=str)
])
class OutputAssertion(Assertion):
    def render(self):
        return string.Template(self.expected).substitute(self.variables)

    def uphold(self, actual):
        return self.render() == actual


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=str)
])
class OutputStartswithAssertion(Assertion):
    def render(self):
        return string.Template(self.expected).substitute(self.variables)

    def uphold(self, actual):
        return actual.startswith(self.render())


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("expected", instance_of=str)
])
class RegexOutputAssertion(Assertion):
    def render(self):
        return string.Template(self.expected).substitute(self.variables)

    def uphold(self, actual):
        return re.compile(self.render()).search(actual.rstrip()) is not None
