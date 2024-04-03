import dataclasses
import textwrap
import typing as t

import termcolor
import typing_extensions as te

LiteralValue = t.Union[None, bool, int, float, str]


def _no_color(text: str, *args: t.Any, **kwargs: t.Any) -> str:
    return text


def pformat(value: t.Union[LiteralValue, "Node"], colored: bool = False) -> str:
    _ = termcolor.colored if colored else _no_color
    if isinstance(value, Node):
        return value.pformat(colored)
    if isinstance(value, str):
        return t.cast(str, _(repr(value), "yellow"))
    else:
        return t.cast(str, _(repr(value), "cyan"))


def pformat_list(values: t.List["Expression"], colored: bool = False) -> str:
    result = ""
    if values:
        for value in values:
            result += "\n" + textwrap.indent(pformat(value, colored), "  ") + ","
        result += "\n"
    return result


def indent_but_first_line(text: str, indent: str) -> str:
    lines = text.splitlines()
    if not lines:
        return ""
    return lines[0] + "\n" + textwrap.indent("\n".join(lines[1:]), indent)


class Node:
    """Base class for HCL2 AST nodes."""

    def pformat_field(self, field_name: str, colored: bool) -> str:
        value = getattr(self, field_name)
        if isinstance(value, Expression):
            formatted = value.pformat(colored)
        elif isinstance(value, list):
            formatted = f"[{pformat_list(value, colored)}]"
        else:
            formatted = pformat(value, colored)
        return formatted

    def pformat(self, colored: bool = True) -> str:
        _ = termcolor.colored if colored else _no_color
        args = []
        fields = dataclasses.fields(self)
        for field in fields:
            args.append(_(field.name, "cyan") + "=" + self.pformat_field(field.name, colored))
        if any("\n" in arg for arg in args) and len(args) > 1:
            sep = ",\n"
            args_string = f'(\n{sep.join(textwrap.indent(arg, "  ") for arg in args)}\n)'
        else:
            args_string = f'({", ".join(args)})'
        return f"{_(type(self).__name__, 'blue')}{args_string}"


class Expression(Node):
    """Base class for nodes that represent expressions in HCL2."""


@dataclasses.dataclass
class Literal(Expression):
    value: LiteralValue

    def __post_init__(self) -> None:
        assert isinstance(self.value, (type(None), bool, int, float, str)), self.value

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return _(repr(self.value), "cyan")


@dataclasses.dataclass
class Array(Expression):
    values: t.List[Expression]


@dataclasses.dataclass
class Object(Expression):
    fields: t.Dict[str, Expression]

    def pformat_field(self, field_name: str, colored: bool) -> str:
        if field_name == "fields":
            if not self.fields:
                return "{}"
            result = "{"
            for key, value in self.fields.items():
                result += f'\n  {pformat(key)}: {indent_but_first_line(value.pformat(colored), "  ")}'
            return result + "}"
        return super().pformat_field(field_name, colored)


@dataclasses.dataclass
class FunctionCall(Expression):
    name: str
    args: t.List[Expression]

    def __post_init__(self) -> None:
        assert all(isinstance(arg, Expression) for arg in self.args), self.args


@dataclasses.dataclass
class Identifier(Expression):
    name: str

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return _(self.name, "yellow")


@dataclasses.dataclass
class GetAttr(Expression):
    on: Expression
    name: str


@dataclasses.dataclass
class GetIndex(Expression):
    on: Expression
    index: Literal


@dataclasses.dataclass
class AttrSplat(Expression):
    on: Expression


@dataclasses.dataclass
class IndexSplat(Expression):
    on: Expression


@dataclasses.dataclass
class UnaryOp(Expression):
    op: te.Literal["-", "!"]
    expr: Expression


@dataclasses.dataclass
class BinaryOp(Expression):
    op: te.Literal["==", "!=", "<", ">", "<=", ">=", "-", "*", "/", "%", "&&", "||", "+"]
    left: Expression
    right: Expression

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return f"({self.left.pformat(colored)} {self.op} {self.right.pformat(colored)})"


@dataclasses.dataclass
class Conditional(Expression):
    cond: Expression
    then_expr: Expression
    else_expr: Expression

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return f"({self.cond.pformat(colored)} ? {self.then_expr.pformat(colored)} : {self.else_expr.pformat(colored)})"


class Stmt(Node):
    """Base class for nodes that represent statements in HCL2."""


@dataclasses.dataclass
class Attribute(Stmt):
    key: str
    value: Expression

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return f"{_(self.key, 'yellow')} = {self.value.pformat(colored)}"


@dataclasses.dataclass
class Block(Stmt):
    name: str
    args: t.List[Expression]
    body: t.List[Stmt]


@dataclasses.dataclass
class Module(Node):
    body: t.List[Stmt]
