import os.path
import shutil
import string
import tempfile

from characteristic import Attribute, attributes

from .exceptions import InvalidRegistrationVariable, NousagiTestError


@attributes([
    Attribute("variables", instance_of=dict),
    Attribute("environ", instance_of=dict),
])
class State(object):
    pass


@attributes([
    Attribute("name", instance_of=str),
    Attribute("attribute", instance_of=str),
])
class RegisterVariable(object):
    """Placeholder for registering variables from command output."""
    @classmethod
    def from_json_dict(cls, data):
        return cls(name=data["name"], attribute=data["attribute"])


class Run(object):
    pass


class Command(Run):
    def __init__(self, func, return_state_klass, registers=None):
        self._func = func
        self._return_state_klass = return_state_klass
        self._registers = registers or []

        for register in self._registers:
            self._return_state_klass.validate(register)

    def register(self, return_state):
        assert isinstance(return_state, self._return_state_klass)

        ret = {}
        for register in self._registers:
            ret.update(return_state.register(register))
        return ret

    def run(self, state):
        return self._func(state)

    def update(self, state, return_state):
        state.variables.update(self.register(return_state))


@attributes(["name", "value"])
class Env(Run):
    @attributes(["env"])
    class ReturnState(object):
        @classmethod
        def validate(cls, variable):
            pass

        def cleanup(self):
            pass

    @classmethod
    def from_json_dict(cls, json_data):
        return cls(name=json_data["name"], value=json_data["value"])

    def run(self, state):
        value = string.Template(self.value).substitute(**state.variables)

        return_state = self.ReturnState(env={self.name: value})
        return return_state

    def update(self, state, return_state):
        state.environ.update(return_state.env)


@attributes([Attribute("steps", instance_of=list)])
class MultiSteps(Run):
    @attributes(["states"])
    class ReturnState(object):
        @classmethod
        def validate(cls, variable):
            pass

        def cleanup(self):
            pass

    def run(self, state):
        return_states = []
        for step in self.steps:
            return_state = step.run(state)
            step.update(state, return_state)
            return_states.append(return_state)

        return_state = self.ReturnState(states=return_states)
        return return_state

    def update(self, state, return_state):
        for i, step in enumerate(self.steps):
            step.update(state, return_state.states[i])


class Mkdtemp(object):
    @attributes(["path"])
    class ReturnState(object):
        @classmethod
        def validate(cls, variable):
            attribute_names = tuple(
                attribute.name for attribute in cls.characteristic_attributes
            )
            if variable.attribute not in attribute_names:
                msg = "Invalid value name {0!r} (must be one of {1})"
                raise InvalidRegistrationVariable(
                    msg.format(variable.attribute, "|".join(attribute_names))
                )

        def cleanup(self):
            shutil.rmtree(self.path)

        def register(self, register):
            return {register.name: getattr(self, register.attribute)}

    @classmethod
    def from_json_dict(cls, json_data):
        return cls()

    def __call__(self, state):
        path = tempfile.mkdtemp()
        return_state = self.ReturnState(path=path)
        return return_state


@attributes(["target", "template"])
class WriteFileFromTemplate(object):
    @attributes([])
    class ReturnState(object):
        @classmethod
        def validate(cls, variable):
            pass

        def cleanup(self):
            pass

        def register(self, register):
            return {}

    @classmethod
    def from_json_dict(cls, json_data):
        source_data = json_data["source"]
        kind = source_data.get("type", "template")
        if kind == "template":
            source = source_data["file"]
            if not os.path.exists(source):
                msg = "file {!r} not found".format(source)
                raise NousagiTestError(msg)
        return cls(target=json_data["target"], template=source)

    def __call__(self, state):
        target = string.Template(self.target).substitute(**state.variables)
        source = string.Template(self.template).substitute(**state.variables)

        with open(source, "rt") as fp:
            template = string.Template(fp.read())
        with open(target, "wt") as fp:
            fp.write(template.substitute(**state.variables))

        return_state = self.ReturnState()
        return return_state


def pre_run_factory_from_json_dict(data):
    commands = {
        "mkdtemp": Mkdtemp,
        "write_file": WriteFileFromTemplate,
    }

    if data["type"] == "command":
        command_klass = commands.get(data["command"])
        if command_klass is None:
            msg = "Unknown command {!r}".format(command_klass)
            raise NotImplementedError(msg)
        command = command_klass.from_json_dict(data)

        registers_data = data.get("register", [])

        registers = tuple(
            RegisterVariable.from_json_dict(register_data)
            for register_data in registers_data
        )

        pre_run = Command(command, command.ReturnState, registers)
    elif data["type"] == "env":
        pre_run = Env.from_json_dict(data)
    else:
        msg = ("Unsupported type of pre run: {!r}".format(data["type"]))
        raise NotImplementedError(msg)

    return pre_run
