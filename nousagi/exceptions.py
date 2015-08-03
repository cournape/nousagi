class NousagiTestError(Exception):
    pass


class YamlParseError(NousagiTestError):
    pass


class JqCompileError(NousagiTestError):
    pass


class InvalidAssertionClass(NousagiTestError):
    pass


class InvalidParameterClass(NousagiTestError):
    pass


class InvalidVariable(NousagiTestError):
    pass


class InvalidVariableType(NousagiTestError):
    pass


class VariableLoopError(NousagiTestError):
    pass
