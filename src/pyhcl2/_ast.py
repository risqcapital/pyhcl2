import dataclasses
import textwrap
from dataclasses import dataclass
from typing import Union, cast

import termcolor
import typing_extensions as te

LiteralValue = None | bool | int | float | str


def _no_color(text: str, *_args: any, **_kwargs: any) -> str:
    return text


def pformat(value: Union[LiteralValue, "Node"], colored: bool = False) -> str:
    _ = termcolor.colored if colored else _no_color
    if isinstance(value, Node):
        return value.pformat(colored)
    if isinstance(value, str):
        return cast(str, _(repr(value), "yellow"))
    else:
        return cast(str, _(repr(value), "cyan"))


def pformat_list(values: list["Expression"], colored: bool = False) -> str:
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


@dataclass(frozen=True, eq=True)
class Literal(Expression):
    value: LiteralValue

    def __post_init__(self) -> None:
        assert isinstance(self.value, (type(None), bool, int, float, str)), self.value

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return _(repr(self.value), "cyan")


@dataclass(frozen=True, eq=True)
class Array(Expression):
    values: list[Expression]


@dataclass(frozen=True, eq=True)
class Object(Expression):
    fields: dict[Expression, Expression]

    def pformat_field(self, field_name: str, colored: bool) -> str:
        if field_name == "fields":
            if not self.fields:
                return "{}"
            result = "{"
            for key, value in self.fields.items():
                result += f'\n  {pformat(key)}: {indent_but_first_line(value.pformat(colored), "  ")}'
            return result + "}"
        return super().pformat_field(field_name, colored)


@dataclass(frozen=True, eq=True)
class Identifier(Expression):
    name: str

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return _(self.name, "yellow")


@dataclass(frozen=True, eq=True)
class FunctionCall(Expression):
    ident: Identifier
    args: list[Expression]
    var_args: bool = False

    def __post_init__(self) -> None:
        assert all(isinstance(arg, Expression) for arg in self.args), self.args


@dataclass(frozen=True, eq=True)
class GetAttrKey(Node):
    ident: Identifier


@dataclass(frozen=True, eq=True)
class GetIndexKey(Node):
    expr: Expression


@dataclass(frozen=True, eq=True)
class GetAttr(Expression):
    on: Expression
    key: GetAttrKey


@dataclass(frozen=True, eq=True)
class GetIndex(Expression):
    on: Expression
    key: GetIndexKey


@dataclass(frozen=True, eq=True)
class AttrSplat(Expression):
    on: Expression
    keys: list[GetAttrKey] = dataclasses.field(default_factory=list)


@dataclass(frozen=True, eq=True)
class IndexSplat(Expression):
    on: Expression
    keys: list[GetAttrKey | GetIndexKey] = dataclasses.field(default_factory=list)


@dataclass(frozen=True, eq=True)
class UnaryOp(Expression):
    op: te.Literal["-", "!"]
    expr: Expression


@dataclass(frozen=True, eq=True)
class BinaryOp(Expression):
    op: te.Literal["==", "!=", "<", ">", "<=", ">=", "-", "*", "/", "%", "&&", "||", "+"]
    left: Expression
    right: Expression

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return f"({self.left.pformat(colored)} {self.op} {self.right.pformat(colored)})"


@dataclass(frozen=True, eq=True)
class Conditional(Expression):
    cond: Expression
    then_expr: Expression
    else_expr: Expression

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return f"({self.cond.pformat(colored)} ? {self.then_expr.pformat(colored)} : {self.else_expr.pformat(colored)})"


@dataclass(frozen=True, eq=True)
class Parenthesis(Expression):
    expr: Expression

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return f"({self.expr.pformat(colored)})"


@dataclass(frozen=True, eq=True)
class ForTupleExpression(Expression):
    key_ident: Identifier | None
    value_ident: Identifier
    collection: Expression
    value: Expression
    condition: Expression | None


@dataclass(frozen=True, eq=True)
class ForObjectExpression(Expression):
    key_ident: Identifier | None
    value_ident: Identifier
    collection: Expression
    key: Expression
    value: Expression
    condition: Expression | None
    grouping_mode: bool = dataclasses.field(default=False)


class Stmt(Node):
    """Base class for nodes that represent statements in HCL2."""


@dataclass(frozen=True, eq=True)
class Attribute(Stmt):
    key: str
    value: Expression

    # def pformat(self, colored: bool = True) -> str:
    #     _ = termcolor.colored if colored else _no_color
    #     return f"{_(self.key, 'yellow')} = {self.value.pformat(colored)}"


@dataclass(frozen=True, eq=True)
class Block(Stmt):
    type: str
    labels: list[Literal | Identifier]
    body: list[Stmt]

    def key(self) -> tuple[str, ...]:
        return tuple([self.type] + [label.name if isinstance(label, Identifier) else label.value if isinstance(label, Literal) else None for label in self.labels])


@dataclass(frozen=True, eq=True)
class Module(Node):
    body: list[Stmt]
